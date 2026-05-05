import json
from typing import Any

import httpx

from app.core.config import settings


class VectorStoreNotConfigured(RuntimeError):
    """Raised when Cloudflare Vectorize credentials aren't set in the env."""


class VectorStore:
    """Cloudflare Vectorize REST client."""

    BASE = "https://api.cloudflare.com/client/v4"

    def __init__(self) -> None:
        self.account_id = settings.CLOUDFLARE_ACCOUNT_ID
        self.api_token = settings.CLOUDFLARE_API_TOKEN
        self.index = settings.CLOUDFLARE_VECTORIZE_INDEX

    def _require_config(self) -> None:
        if not (self.account_id and self.api_token and self.index):
            raise VectorStoreNotConfigured(
                "CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN / "
                "CLOUDFLARE_VECTORIZE_INDEX must be set in the environment."
            )

    def _query_url(self) -> str:
        return (
            f"{self.BASE}/accounts/{self.account_id}"
            f"/vectorize/v2/indexes/{self.index}/query"
        )

    def _upsert_url(self) -> str:
        return (
            f"{self.BASE}/accounts/{self.account_id}"
            f"/vectorize/v2/indexes/{self.index}/upsert"
        )

    def _delete_url(self) -> str:
        # Cloudflare's V2 API uses underscore here, unlike most other paths.
        # Hyphenated `delete-by-ids` 404s.
        return (
            f"{self.BASE}/accounts/{self.account_id}"
            f"/vectorize/v2/indexes/{self.index}/delete_by_ids"
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def query(
        self,
        vector: list[float],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """Return up to `top_k` nearest matches to `vector`.

        Each match has keys: `id` (str), `score` (float), `metadata` (dict).
        Metadata shape depends on what was stored at upsert time; callers
        should treat missing keys defensively.
        """
        self._require_config()

        body = {"vector": vector, "topK": top_k, "returnMetadata": "all"}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                self._query_url(), headers=self._headers(), json=body
            )
        resp.raise_for_status()
        return resp.json().get("result", {}).get("matches", [])

    async def upsert(
        self,
        items: list[dict[str, Any]],
    ) -> None:
        """Insert-or-update vectors. Each item: {id, values, metadata?}.

        Cloudflare's upsert endpoint takes NDJSON (one JSON object per line)
        rather than a JSON array, which is why we serialize manually.
        """
        if not items:
            return
        self._require_config()

        ndjson = "\n".join(json.dumps(it) for it in items)
        headers = self._headers() | {"Content-Type": "application/x-ndjson"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                self._upsert_url(), headers=headers, content=ndjson
            )
        resp.raise_for_status()

    async def delete(self, ids: list[str]) -> None:
        """Remove vectors by id."""
        if not ids:
            return
        self._require_config()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                self._delete_url(),
                headers=self._headers(),
                json={"ids": ids},
            )
        resp.raise_for_status()


vector_store = VectorStore()
