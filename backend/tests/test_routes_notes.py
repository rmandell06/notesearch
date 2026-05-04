from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import embedding as embedding_module
from app.services import supabase_client as supabase_module
from app.services import vector_store as vs_module


AUTH = {"Authorization": "Bearer test-token"}


@pytest.fixture(autouse=True)
def stub_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip the real Supabase JWT validation — every request is user 'u-1'."""
    fake = MagicMock()
    fake.auth.get_user = AsyncMock(
        return_value=SimpleNamespace(user=SimpleNamespace(id="u-1"))
    )
    monkeypatch.setattr(
        supabase_module.supabase_client,
        "client",
        AsyncMock(return_value=fake),
    )
    # Return the same fake from the auth-validating call so route code that
    # also reaches into client.table(...) works (chained mock below).
    return fake


@pytest.fixture
def fake_table(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Builder-style mock so `client.table(...).insert(...).execute()` works."""
    chain = MagicMock()
    # Every chained method returns the same chain so we don't have to set up
    # each link individually. `execute` is the awaitable that yields data.
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
    embed = MagicMock(return_value=[[0.1] * 128])
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


def _row() -> dict:
    return {
        "id": "n-1",
        "title": "Hi",
        "content": "Body",
        "created_at": "2026-04-25T00:00:00",
        "source": "text",
    }


def test_create_note_persists_and_indexes(
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
    stub_vector_upsert.assert_awaited_once()
    (sent_items,) = stub_vector_upsert.await_args.args
    assert sent_items[0]["id"] == "n-1"
    assert sent_items[0]["metadata"]["user_id"] == "u-1"


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


def test_delete_note_drops_vector(
    client, fake_table: MagicMock, stub_vector_delete: AsyncMock
) -> None:
    fake_table.execute.return_value = SimpleNamespace(data=[_row()])

    resp = client.delete("/notes/n-1", headers=AUTH)
    assert resp.status_code == 200
    stub_vector_delete.assert_awaited_once_with(["n-1"])


def test_missing_auth_header_401(client) -> None:
    resp = client.get("/notes/")
    assert resp.status_code == 401
