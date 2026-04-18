from app.core.config import settings


class SupabaseClient:
    """Wraps the Supabase notes table and auth endpoints."""

    def __init__(self) -> None:
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY


supabase_client = SupabaseClient()
