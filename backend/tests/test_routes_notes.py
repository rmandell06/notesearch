import io
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import embedding as embedding_module
from app.services import storage as storage_module
from app.services import supabase_client as supabase_module
from app.services import vector_store as vs_module


AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture(autouse=True)
def stub_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = MagicMock()
    fake.auth.get_user = AsyncMock(
        return_value=SimpleNamespace(user=SimpleNamespace(id="u-1"))
    )
    monkeypatch.setattr(
        supabase_module.supabase_client,
        "client",
        AsyncMock(return_value=fake),
    )
    return fake


@pytest.fixture
def fake_table(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    chain = MagicMock()
    chain.insert.return_value = chain
    chain.select.return_value = chain
    chain.delete.return_value = chain
    chain.eq.return_value = chain
    chain.order.return_value = chain
    chain.single.return_value = chain
    chain.limit.return_value = chain
    chain.execute = AsyncMock()

    fake = MagicMock()
    fake.auth.get_user = AsyncMock(
        return_value=SimpleNamespace(user=SimpleNamespace(id="u-1"))
    )
    fake.table.return_value = chain

    monkeypatch.setattr(
        supabase_module.supabase_client,
        "client",
        AsyncMock(return_value=fake),
    )
    return chain


@pytest.fixture
def stub_embed(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    embed = MagicMock(side_effect=lambda texts: [[0.1] * 128 for _ in texts])
    monkeypatch.setattr(embedding_module.embedding_service, "embed", embed)
    return embed


@pytest.fixture
def stub_vector_upsert(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    upsert = AsyncMock()
    monkeypatch.setattr(vs_module.vector_store, "upsert", upsert)
    return upsert


@pytest.fixture
def stub_vector_delete(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    delete = AsyncMock()
    monkeypatch.setattr(vs_module.vector_store, "delete", delete)
    return delete


@pytest.fixture
def stub_storage(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    save = AsyncMock(return_value=("key-1", "checksum"))
    delete = AsyncMock()
    monkeypatch.setattr(storage_module.storage_service, "save", save)
    monkeypatch.setattr(storage_module.storage_service, "delete", delete)
    return MagicMock(save=save, delete=delete)


def _row(**overrides) -> dict:
    base = {
        "id": "n-1",
        "title": "Hi",
        "content": "Body",
        "created_at": "2026-04-25T00:00:00",
        "source": "text",
        "chunk_count": 1,
        "storage_key": None,
    }
    base.update(overrides)
    return base


def test_short_note_indexes_as_single_chunk(
    client,
    fake_table: MagicMock,
    stub_embed: MagicMock,
    stub_vector_upsert: AsyncMock,
) -> None:
    fake_table.execute.return_value = SimpleNamespace(data=[_row()])

    resp = client.post(
        "/notes/", headers=AUTH, json={"title": "Hi", "content": "Body"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == "n-1"
    assert body["preview"] == "Body"
    assert body["date"] == "Apr 25, 2026"
    assert body["body"] == "Body"

    stub_embed.assert_called_once_with(["Hi\nBody"])
    (sent_items,) = stub_vector_upsert.await_args.args
    assert len(sent_items) == 1
    md = sent_items[0]["metadata"]
    assert md["note_id"] == "n-1"
    assert md["chunk_index"] == 0
    assert md["user_id"] == "u-1"
    assert md["created_at"] == "2026-04-25T00:00:00"


def test_long_note_indexes_as_multiple_chunks(
    client,
    fake_table: MagicMock,
    stub_embed: MagicMock,
    stub_vector_upsert: AsyncMock,
) -> None:
    long_content = " ".join(["word"] * 600)
    fake_table.execute.return_value = SimpleNamespace(data=[_row(chunk_count=4)])

    resp = client.post(
        "/notes/",
        headers=AUTH,
        json={"title": "Hi", "content": long_content},
    )
    assert resp.status_code == 200

    # Multi-chunk path batches everything in one call:
    #   [title, *chunks, *(title+chunk_i)]  → 2N + 1 vectors
    # Only the search vectors (N at the end) get upserted.
    (embedded_texts,) = stub_embed.call_args.args
    assert embedded_texts[0] == "Hi"  # title goes first
    n_chunks = (len(embedded_texts) - 1) // 2
    assert n_chunks >= 3
    (sent_items,) = stub_vector_upsert.await_args.args
    assert len(sent_items) == n_chunks
    assert [it["id"] for it in sent_items] == [
        f"n-1::{i}" for i in range(n_chunks)
    ]


def test_upload_endpoint_extracts_text_and_indexes(
    client,
    fake_table: MagicMock,
    stub_embed: MagicMock,
    stub_vector_upsert: AsyncMock,
    stub_storage: MagicMock,
) -> None:
    fake_table.execute.return_value = SimpleNamespace(
        data=[_row(source="upload", storage_key="key-1", content="hello world")]
    )
    file_bytes = b"hello world"

    resp = client.post(
        "/notes/upload",
        headers=AUTH,
        files={"file": ("note.txt", io.BytesIO(file_bytes), "text/plain")},
        data={"title": "Custom"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"id": "n-1", "title": "Custom", "status": "uploaded"}

    stub_storage.save.assert_awaited_once()
    stub_embed.assert_called_once()
    stub_vector_upsert.assert_awaited_once()


def test_upload_uses_filename_when_title_missing(
    client,
    fake_table: MagicMock,
    stub_embed: MagicMock,
    stub_vector_upsert: AsyncMock,
    stub_storage: MagicMock,
) -> None:
    fake_table.execute.return_value = SimpleNamespace(
        data=[_row(source="upload", storage_key="key-1")]
    )
    resp = client.post(
        "/notes/upload",
        headers=AUTH,
        files={"file": ("doc.txt", io.BytesIO(b"x"), "text/plain")},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "doc.txt"


def test_list_notes_returns_display_fields(
    client, fake_table: MagicMock
) -> None:
    fake_table.execute.return_value = SimpleNamespace(
        data=[_row(content="some long content that should be truncated nicely" * 10)]
    )

    resp = client.get("/notes/", headers=AUTH)
    assert resp.status_code == 200
    [item] = resp.json()
    assert item["id"] == "n-1"
    # Long content with no stored preview falls back to truncated content + ellipsis.
    assert item["preview"].endswith("…")
    assert item["date"] == "Apr 25, 2026"
    fake_table.eq.assert_any_call("user_id", "u-1")
    fake_table.limit.assert_called_with(10)


def test_get_note_returns_body_for_detail_view(
    client, fake_table: MagicMock
) -> None:
    fake_table.execute.return_value = SimpleNamespace(data=_row(content="full body"))

    resp = client.get("/notes/n-1", headers=AUTH)
    assert resp.status_code == 200
    body = resp.json()
    assert body["body"] == "full body"
    assert body["content"] == "full body"


def test_get_note_404_when_missing(client, fake_table: MagicMock) -> None:
    fake_table.execute.return_value = SimpleNamespace(data=None)

    resp = client.get("/notes/n-1", headers=AUTH)
    assert resp.status_code == 404


def test_delete_note_drops_all_chunk_vectors(
    client,
    fake_table: MagicMock,
    stub_vector_delete: AsyncMock,
    stub_storage: MagicMock,
) -> None:
    fake_table.execute.return_value = SimpleNamespace(
        data=[_row(chunk_count=3, storage_key="key-1")]
    )

    resp = client.delete("/notes/n-1", headers=AUTH)
    assert resp.status_code == 200
    stub_vector_delete.assert_awaited_once_with(["n-1::0", "n-1::1", "n-1::2"])
    stub_storage.delete.assert_awaited_once_with("key-1")


def test_delete_legacy_note_falls_back_to_bare_id(
    client, fake_table: MagicMock, stub_vector_delete: AsyncMock
) -> None:
    legacy_row = {
        "id": "n-1",
        "title": "Hi",
        "content": "Body",
        "created_at": "2026-04-25T00:00:00",
        "source": "text",
    }
    fake_table.execute.return_value = SimpleNamespace(data=[legacy_row])

    resp = client.delete("/notes/n-1", headers=AUTH)
    assert resp.status_code == 200
    stub_vector_delete.assert_awaited_once_with(["n-1"])


def test_missing_auth_header_401(client) -> None:
    resp = client.get("/notes/")
    assert resp.status_code == 401
