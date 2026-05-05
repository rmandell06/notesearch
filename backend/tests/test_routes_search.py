from unittest.mock import AsyncMock

import pytest

from app.services import vector_store as vector_store_module
from app.services.vector_store import VectorStoreNotConfigured


@pytest.fixture
def stub_query(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Replace the live Cloudflare call with an AsyncMock the test can drive."""
    mock = AsyncMock()
    monkeypatch.setattr(vector_store_module.vector_store, "query", mock)
    return mock


def test_returns_results_from_vector_store(client, stub_query: AsyncMock) -> None:
    stub_query.return_value = [
        {
            "id": "note-1::0",
            "score": 0.95,
            "metadata": {"note_id": "note-1", "title": "First"},
        },
        {
            "id": "note-2::0",
            "score": 0.82,
            "metadata": {"note_id": "note-2", "title": "Second"},
        },
    ]

    resp = client.get("/search/", params={"q": "hello"})
    assert resp.status_code == 200
    assert resp.json() == [
        {"note_id": "note-1", "title": "First", "score": 0.95},
        {"note_id": "note-2", "title": "Second", "score": 0.82},
    ]
    stub_query.assert_awaited_once()
    (sent_vector,) = stub_query.await_args.args
    assert isinstance(sent_vector, list)
    assert len(sent_vector) == 128
    # Search asks for top_k * OVERSAMPLE so chunk dedup has room to work.
    assert stub_query.await_args.kwargs["top_k"] >= 10


def test_dedupes_chunks_to_one_per_note_keeping_best_score(
    client, stub_query: AsyncMock
) -> None:
    """Three chunks of the same note should collapse to one result with the
    highest score."""
    stub_query.return_value = [
        {"id": "n-1::0", "score": 0.91, "metadata": {"note_id": "n-1", "title": "A"}},
        {"id": "n-1::2", "score": 0.95, "metadata": {"note_id": "n-1", "title": "A"}},
        {"id": "n-2::0", "score": 0.80, "metadata": {"note_id": "n-2", "title": "B"}},
        {"id": "n-1::1", "score": 0.70, "metadata": {"note_id": "n-1", "title": "A"}},
    ]

    resp = client.get("/search/", params={"q": "x"})
    assert resp.status_code == 200
    assert resp.json() == [
        {"note_id": "n-1", "title": "A", "score": 0.95},
        {"note_id": "n-2", "title": "B", "score": 0.80},
    ]


def test_falls_back_to_bare_id_for_legacy_entries(
    client, stub_query: AsyncMock
) -> None:
    """Vectors uploaded before chunking have no metadata.note_id."""
    stub_query.return_value = [
        {"id": "legacy-1", "score": 0.7, "metadata": {"title": "Old"}},
    ]

    resp = client.get("/search/", params={"q": "x"})
    assert resp.status_code == 200
    assert resp.json() == [
        {"note_id": "legacy-1", "title": "Old", "score": 0.7},
    ]


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


def test_missing_metadata_falls_back_to_blank_title(
    client, stub_query: AsyncMock
) -> None:
    stub_query.return_value = [{"id": "note-3", "score": 0.5, "metadata": {}}]

    resp = client.get("/search/", params={"q": "x"})
    assert resp.status_code == 200
    assert resp.json() == [{"note_id": "note-3", "title": "", "score": 0.5}]


def test_top_k_caps_returned_results_after_dedupe(
    client, stub_query: AsyncMock
) -> None:
    stub_query.return_value = [
        {"id": f"n-{i}::0", "score": 0.9 - 0.01 * i, "metadata": {"note_id": f"n-{i}", "title": ""}}
        for i in range(15)
    ]

    resp = client.get("/search/", params={"q": "x", "top_k": 3})
    assert resp.status_code == 200
    assert len(resp.json()) == 3
