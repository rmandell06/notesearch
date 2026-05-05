import json

import pytest

from app.services import vector_store as vs_module
from app.services.vector_store import VectorStoreNotConfigured


class _FakeResp:
    def __init__(self, payload: dict, status: int = 200) -> None:
        self._payload = payload
        self.status_code = status

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return self._payload


@pytest.fixture
def fake_httpx(monkeypatch: pytest.MonkeyPatch) -> dict:
    """Replace httpx.AsyncClient with one that captures POSTs and returns a
    canned payload. Returns a dict the test can mutate to drive responses."""
    state = {
        "calls": [],
        "response_payload": {"result": {"matches": []}},
    }

    class FakeClient:
        def __init__(self, **kw):
            pass

        async def __aenter__(self) -> "FakeClient":
            return self

        async def __aexit__(self, *args) -> None:
            return None

        async def post(self, url, headers=None, json=None, content=None) -> _FakeResp:
            state["calls"].append(
                {"url": url, "headers": headers, "json": json, "content": content}
            )
            return _FakeResp(state["response_payload"])

    monkeypatch.setattr("app.services.vector_store.httpx.AsyncClient", FakeClient)
    # Make the live VectorStore think it's configured.
    monkeypatch.setattr(vs_module.vector_store, "account_id", "acct")
    monkeypatch.setattr(vs_module.vector_store, "api_token", "tok")
    monkeypatch.setattr(vs_module.vector_store, "index", "idx")
    return state


@pytest.mark.asyncio
async def test_query_posts_to_correct_url_and_parses_matches(
    fake_httpx: dict,
) -> None:
    fake_httpx["response_payload"] = {
        "result": {"matches": [{"id": "v-1", "score": 0.9, "metadata": {}}]}
    }

    result = await vs_module.vector_store.query([0.1] * 128, top_k=5)

    assert result == [{"id": "v-1", "score": 0.9, "metadata": {}}]
    [call] = fake_httpx["calls"]
    assert call["url"].endswith("/vectorize/v2/indexes/idx/query")
    assert call["headers"]["Authorization"] == "Bearer tok"
    assert call["json"]["topK"] == 5
    assert call["json"]["returnMetadata"] == "all"


@pytest.mark.asyncio
async def test_upsert_serializes_ndjson(fake_httpx: dict) -> None:
    items = [
        {"id": "a", "values": [0.1, 0.2], "metadata": {"k": "v"}},
        {"id": "b", "values": [0.3, 0.4]},
    ]

    await vs_module.vector_store.upsert(items)

    [call] = fake_httpx["calls"]
    assert call["url"].endswith("/upsert")
    assert call["headers"]["Content-Type"] == "application/x-ndjson"
    # Each line is one JSON object.
    lines = call["content"].split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0]) == items[0]
    assert json.loads(lines[1]) == items[1]


@pytest.mark.asyncio
async def test_upsert_skips_when_empty(fake_httpx: dict) -> None:
    await vs_module.vector_store.upsert([])
    assert fake_httpx["calls"] == []


@pytest.mark.asyncio
async def test_delete_posts_id_list(fake_httpx: dict) -> None:
    await vs_module.vector_store.delete(["v-1", "v-2"])

    [call] = fake_httpx["calls"]
    assert call["url"].endswith("/delete-by-ids")
    assert call["json"] == {"ids": ["v-1", "v-2"]}


@pytest.mark.asyncio
async def test_delete_skips_when_empty(fake_httpx: dict) -> None:
    await vs_module.vector_store.delete([])
    assert fake_httpx["calls"] == []


@pytest.mark.asyncio
async def test_raises_when_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(vs_module.vector_store, "account_id", "")
    with pytest.raises(VectorStoreNotConfigured):
        await vs_module.vector_store.query([0.1] * 128, top_k=1)
    with pytest.raises(VectorStoreNotConfigured):
        await vs_module.vector_store.upsert([{"id": "x", "values": [0.1]}])
    with pytest.raises(VectorStoreNotConfigured):
        await vs_module.vector_store.delete(["x"])
