class EmbeddingService:
    """Loads the frozen 256-dim encoder and produces sentence embeddings."""

    def __init__(self) -> None:
        self.model = None

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


embedding_service = EmbeddingService()
