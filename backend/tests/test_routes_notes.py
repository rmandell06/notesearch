from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import embedding as embedding_module
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
    """Returns one fake vector per input text (so chunked notes get N vectors)."""
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


def _row(chunk_count: int = 1, content: str = "Body") -> dict:
    return {
        "id": "n-1",
        "title": "Hi",
        "content": content,
        "created_at": "2026-04-25T00:00:00",
        "source": "text",
        "chunk_count": chunk_count,
    }


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
    assert resp.json()["id"] == "n-1"

    stub_embed.assert_called_once_with(["Hi\nBody"])
    (sent_items,) = stub_vector_upsert.await_args.args
    assert len(sent_items) == 1
    assert sent_items[0]["id"] == "n-1::0"
    assert sent_items[0]["metadata"]["note_id"] == "n-1"
    assert sent_items[0]["metadata"]["chunk_index"] == 0
    assert sent_items[0]["metadata"]["user_id"] == "u-1"


def test_long_note_indexes_as_multiple_chunks(
    client,
    fake_table: MagicMock,
    stub_embed: MagicMock,
    stub_vector_upsert: AsyncMock,
) -> None:
    long_content = " ".join(["word"] * 600)  # 600 words → ~3 chunks
    fake_table.execute.return_value = SimpleNamespace(data=[_row(chunk_count=4)])

    resp = client.post(
        "/notes/",
        headers=AUTH,
        json={"title": "Hi", "content": long_content},
    )
    assert resp.status_code == 200

    (embedded_texts,) = stub_embed.call_args.args
    assert len(embedded_texts) >= 3  # multiple chunks for a 600-word note
    (sent_items,) = stub_vector_upsert.await_args.args
    assert len(sent_items) == len(embedded_texts)
    # Composite ids in order
    assert [it["id"] for it in sent_items] == [
        f"n-1::{i}" for i in range(len(sent_items))
    ]


def test_list_notes_filters_by_user(client, fake_table: MagicMock) -> None:
    fake_table.execute.return_value = SimpleNamespace(data=[_row()])

    resp = client.get("/notes/", headers=AUTH)
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    fake_table.eq.assert_any_call("user_id", "u-1")


def test_get_note_404_when_missing(client, fake_table: MagicMock) -> None:
    fake_table.execute.return_value = SimpleNamespace(data=None)

    resp = client.get("/notes/n-1", headers=AUTH)
    assert resp.status_code == 404


def test_delete_note_drops_all_chunk_vectors(
    client, fake_table: MagicMock, stub_vector_delete: AsyncMock
) -> None:
    fake_table.execute.return_value = SimpleNamespace(data=[_row(chunk_count=3)])

    resp = client.delete("/notes/n-1", headers=AUTH)
    assert resp.status_code == 200
    stub_vector_delete.assert_awaited_once_with(["n-1::0", "n-1::1", "n-1::2"])


def test_delete_legacy_note_falls_back_to_bare_id(
    client, fake_table: MagicMock, stub_vector_delete: AsyncMock
) -> None:
    """Old rows that pre-date chunking have no chunk_count column."""
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
