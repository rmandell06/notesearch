import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Wraps Supabase auth and the notes table.

    Required Supabase table (run in SQL editor):
        CREATE TABLE notes (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            content TEXT NOT NULL DEFAULT '',
            storage_key TEXT,
            source TEXT NOT NULL DEFAULT 'text',
            embedding FLOAT8[],
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
        CREATE POLICY "users_own_notes" ON notes FOR ALL USING (auth.uid() = user_id);
    """

    def __init__(self) -> None:
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self.url or not self.key:
                raise RuntimeError("Supabase not configured: set SUPABASE_URL and SUPABASE_KEY in .env")
            from supabase import create_client
            self._client = create_client(self.url, self.key)
        return self._client

    # ── Auth ──────────────────────────────────────────────────────────────────

    def sign_up(self, email: str, password: str) -> dict:
        client = self._get_client()
        response = client.auth.sign_up({"email": email, "password": password})
        if not response.user:
            raise ValueError("Sign up failed — check Supabase email confirmation settings")
        return {
            "user_id": str(response.user.id),
            "access_token": response.session.access_token if response.session else "",
        }

    def sign_in(self, email: str, password: str) -> dict:
        client = self._get_client()
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        if not response.user:
            raise ValueError("Invalid credentials")
        return {
            "user_id": str(response.user.id),
            "access_token": response.session.access_token,
        }

    def get_user_id(self, token: str) -> str | None:
        try:
            client = self._get_client()
            response = client.auth.get_user(token)
            return str(response.user.id) if response.user else None
        except Exception:
            return None

    # ── Notes CRUD ────────────────────────────────────────────────────────────

    def create_note(
        self,
        user_id: str,
        title: str,
        content: str,
        storage_key: str | None,
        source: str,
    ) -> str:
        client = self._get_client()
        response = client.table("notes").insert({
            "user_id": user_id,
            "title": title,
            "content": content,
            "storage_key": storage_key,
            "source": source,
        }).execute()
        return response.data[0]["id"]

    def update_embedding(self, note_id: str, embedding: list[float]) -> None:
        client = self._get_client()
        client.table("notes").update({"embedding": embedding}).eq("id", note_id).execute()

    def list_notes(self, user_id: str, limit: int = 20) -> list[dict]:
        client = self._get_client()
        response = (
            client.table("notes")
            .select("id,title,content,source,created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data or []

    def get_note(self, note_id: str, user_id: str) -> dict | None:
        client = self._get_client()
        response = (
            client.table("notes")
            .select("id,title,content,source,created_at,storage_key")
            .eq("id", note_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def delete_note(self, note_id: str, user_id: str) -> None:
        client = self._get_client()
        client.table("notes").delete().eq("id", note_id).eq("user_id", user_id).execute()

    def get_notes_with_embeddings(self, user_id: str) -> list[dict]:
        client = self._get_client()
        response = (
            client.table("notes")
            .select("id,title,content,created_at,embedding")
            .eq("user_id", user_id)
            .not_.is_("embedding", "null")
            .execute()
        )
        return response.data or []

    def search_notes(self, user_id: str, query: str, limit: int = 10) -> list[dict]:
        """Full-text search over note titles and content using Postgres ILIKE."""
        client = self._get_client()
        pattern = f"%{query}%"
        # Search titles first (more relevant), then content
        title_hits = (
            client.table("notes")
            .select("id,title,content,source,created_at")
            .eq("user_id", user_id)
            .ilike("title", pattern)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        ).data or []

        content_ids = {r["id"] for r in title_hits}
        content_hits = (
            client.table("notes")
            .select("id,title,content,source,created_at")
            .eq("user_id", user_id)
            .ilike("content", pattern)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        ).data or []

        seen: set[str] = set()
        results: list[dict] = []
        for note in title_hits + content_hits:
            if note["id"] not in seen:
                seen.add(note["id"])
                note["relevance"] = 1.0 if note["id"] in content_ids else 0.7
                results.append(note)

        return results[:limit]

    def get_notes_by_ids(self, note_ids: list[str], user_id: str) -> list[dict]:
        if not note_ids:
            return []
        client = self._get_client()
        response = (
            client.table("notes")
            .select("id,title,content,source,created_at")
            .in_("id", note_ids)
            .eq("user_id", user_id)
            .execute()
        )
        return response.data or []


supabase_client = SupabaseClient()
