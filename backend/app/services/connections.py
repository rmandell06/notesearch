class ConnectionsService:
    """Builds a cosine-similarity graph over stored note vectors for NVL."""

    def build_graph(self, user_id: str, threshold: float = 0.7) -> dict:
        raise NotImplementedError


connections_service = ConnectionsService()
