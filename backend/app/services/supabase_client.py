from supabase import AsyncClient, create_async_client

from app.core.config import settings


class SupabaseNotConfigured(RuntimeError):
    """Raised when Supabase URL/key aren't set in the env."""


class SupabaseClient:
    """Lazy async wrapper around supabase-py. Reuses one client per process."""

    def __init__(self) -> None:
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY
        self._client: AsyncClient | None = None

    async def client(self) -> AsyncClient:
        if not self.url or not self.key:
            raise SupabaseNotConfigured(
                "SUPABASE_URL and SUPABASE_KEY must be set in the environment."
            )
        if self._client is None:
            self._client = await create_async_client(self.url, self.key)
        return self._client


supabase_client = SupabaseClient()
