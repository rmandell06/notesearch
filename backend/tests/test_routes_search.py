from unittest.mock import AsyncMock

import pytest

from app.services import vector_store as vector_store_module
from app.services.vector_store import VectorStoreNotConfigured


@pytest.fixture
def stub_query(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    mock = AsyncMock()
    monkeypatch.setattr(vector_store_module.vector_store, "query", mock)
    return mock


def test_returns_results_with_display_fields(client, stub_query: AsyncMock) -> None:
    stub_query.return_value = [
        {
            "id": "note-1::0",
            "score": 0.95,
            "metadata": {
                "note_id": "note-1",
                "title": "First",
                "snippet": "leading text",
                "created_at": "2026-04-25T00:00:00",
            },
        },
    ]

    resp = client.get("/search/", params={"q": "hello"})
    assert resp.status_code == 200
    [hit] = resp.json()
    assert hit["id"] == "note-1"
    assert hit["note_id"] == "note-1"
    assert hit["title"] == "First"
    assert hit["preview"] == "leading text"
    assert hit["date"] == "Apr 25, 2026"
    assert hit["score"] == 0.95
    assert hit["relevance"] == 0.95


def test_dedupes_chunks_to_one_per_note_keeping_best_score(
    client, stub_query: AsyncMock
) -> None:
    stub_query.return_value = [
        {"id": "n-1::0", "score": 0.91, "metadata": {"note_id": "n-1", "title": "A"}},
        {"id": "n-1::2", "score": 0.95, "metadata": {"note_id": "n-1", "title": "A"}},
        {"id": "n-2::0", "score": 0.80, "metadata": {"note_id": "n-2", "title": "B"}},
        {"id": "n-1::1", "score": 0.70, "metadata": {"note_id": "n-1", "title": "A"}},
    ]

    resp = client.get("/search/", params={"q": "x"})
    assert resp.status_code == 200
    out = resp.json()
    assert len(out) == 2
    assert out[0]["id"] == "n-1"
    assert out[0]["relevance"] == 0.95
    assert out[1]["id"] == "n-2"


def test_falls_back_to_bare_id_for_legacy_entries(
    client, stub_query: AsyncMock
) -> None:
    stub_query.return_value = [
        {"id": "legacy-1", "score": 0.7, "metadata": {"title": "Old"}},
    ]

    resp = client.get("/search/", params={"q": "x"})
    assert resp.status_code == 200
    [hit] = resp.json()
    assert hit["id"] == "legacy-1"


def test_503_when_vector_store_not_configured(
    client, stub_query: AsyncMock
) -> None:
    stub_query.side_effect = VectorStoreNotConfigured("missing creds")

    resp = client.get("/search/", params={"q": "hello"})
    assert resp.status_code == 503
    assert "missing creds" in resp.json()["detail"]


def test_handles_empty_match_list(client, stub_query: AsyncMock) -> None:
    stub_query.return_value = []

    resp = client.get("/search/", params={"q": "obscure query"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_top_k_caps_returned_results_after_dedupe(
    client, stub_query: AsyncMock
) -> None:
    stub_query.return_value = [
        {"id": f"n-{i}::0", "score": 0.9 - 0.01 * i,
         "metadata": {"note_id": f"n-{i}", "title": ""}}
        for i in range(15)
    ]

    resp = client.get("/search/", params={"q": "x", "top_k": 3})
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_oversamples_so_chunk_dedupe_has_room(
    client, stub_query: AsyncMock
) -> None:
    stub_query.return_value = []
    client.get("/search/", params={"q": "x", "top_k": 10})
    # Search asks Cloudflare for top_k * OVERSAMPLE so dedupe doesn't truncate.
    assert stub_query.await_args.kwargs["top_k"] >= 10
