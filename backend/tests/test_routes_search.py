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
        {"id": "note-1", "score": 0.95, "metadata": {"title": "First"}},
        {"id": "note-2", "score": 0.82, "metadata": {"title": "Second"}},
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
    assert len(sent_vector) == 128  # matches Encoder d_model
    assert stub_query.await_args.kwargs["top_k"] == 10


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
