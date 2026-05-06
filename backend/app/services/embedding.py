import logging
from pathlib import Path

import torch
import torch.nn as nn

from app.services.encoder import Encoder
from app.services.tokenizer import BPETokenizer


logger = logging.getLogger(__name__)
ARTIFACTS = Path(__file__).resolve().parents[2] / "artifacts"


def _select_quant_engine() -> str | None:
    """Pick a quantization backend the local torch build supports.

    fbgemm is the default on x86 servers (Render, most Linux clouds);
    qnnpack covers ARM (Apple Silicon laptops, some Render plans). Returns
    None if neither is available, in which case we skip quantization.
    """
    available = set(torch.backends.quantized.supported_engines)
    for eng in ("fbgemm", "qnnpack"):
        if eng in available:
            return eng
    return None


def _quantize(model: Encoder) -> Encoder:
    """Apply dynamic int8 quantization to all nn.Linear layers in the model.

    Memory drops ~3-4× (int8 weights) and Render's free-tier 512 MB ceiling
    becomes survivable. Quality cost is ~1% on the separation metric — well
    below noise floor for retrieval (rankings preserved). See the cosine
    sanity check in our notes if curious.

    If quantization fails for any reason (no qengine, torch build mismatch,
    etc.), log and return the model unchanged rather than crash startup.
    """
    engine = _select_quant_engine()
    if engine is None:
        logger.warning(
            "embedding: no quantization engine available; running fp32. "
            "Free-tier deploys may OOM under load."
        )
        return model
    try:
        torch.backends.quantized.engine = engine
        quantized = torch.quantization.quantize_dynamic(
            model, {nn.Linear}, dtype=torch.qint8
        )
        logger.info("embedding: int8 quantization active (engine=%s)", engine)
        return quantized
    except Exception as exc:  # pragma: no cover  # best-effort fallback
        logger.warning("embedding: quantization failed (%s); using fp32", exc)
        return model


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
            model = Encoder.load(ARTIFACTS, map_location="cpu")
            self._model = _quantize(model)
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
