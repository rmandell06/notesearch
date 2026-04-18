from app.core.config import settings


class VectorStore:
    """Cloudflare Vectorize REST client."""

    def __init__(self) -> None:
        self.account_id = settings.CLOUDFLARE_ACCOUNT_ID
        self.api_token = settings.CLOUDFLARE_API_TOKEN
        self.index = settings.CLOUDFLARE_VECTORIZE_INDEX


vector_store = VectorStore()
