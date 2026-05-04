from pathlib import Path

import torch

from app.services.encoder import Encoder
from app.services.tokenizer import BPETokenizer


ARTIFACTS = Path(__file__).resolve().parents[2] / "artifacts"


class EmbeddingService:
    """Loads the trained encoder + tokenizer and produces sentence embeddings."""

    def __init__(self) -> None:
        # Lazy-loaded on first embed() call to avoid paying ~12 MB of torch
        # load time and 5 MB of vocab.json during plain `import app.main`
        # (e.g. when running unrelated route tests).
        self._model: Encoder | None = None
        self._tokenizer: BPETokenizer | None = None

    def _ensure_loaded(self) -> tuple[BPETokenizer, Encoder]:
        if self._tokenizer is None or self._model is None:
            self._tokenizer = BPETokenizer.from_pretrained(
                ARTIFACTS, vocab_size=10_000
            )
            self._model = Encoder.load(ARTIFACTS, map_location="cpu")
        return self._tokenizer, self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        tokenizer, model = self._ensure_loaded()
        max_seq_len = model.config["max_seq_len"]

        # Tokenize and truncate. An empty input still gets at least one pad
        # token so its row exists in the output (caller passed N texts → wants
        # N vectors).
        sequences: list[list[int]] = []
        for text in texts:
            ids = tokenizer.encode(text)[:max_seq_len]
            if not ids:
                ids = [tokenizer.pad_id]
            sequences.append(ids)

        # Pad to the longest sequence in the batch (no need to pad the whole
        # way to max_seq_len — the encoder handles any length up to the cap).
        batch_len = max(len(s) for s in sequences)
        padded = [s + [tokenizer.pad_id] * (batch_len - len(s)) for s in sequences]

        with torch.no_grad():
            x = torch.tensor(padded, dtype=torch.long)
            vectors = model(x)  # (batch, d_model), already mean-pooled

        return vectors.tolist()


embedding_service = EmbeddingService()
