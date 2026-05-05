from fastapi import APIRouter, HTTPException

from app.schemas.search import SearchResult
from app.services.embedding import embedding_service
from app.services.vector_store import VectorStoreNotConfigured, vector_store


router = APIRouter()

# Notes are split into chunks at index time, so the same note can produce
# multiple matches. Pull more than top_k from Cloudflare and dedupe back down
# to one result per note (keeping the best-scoring chunk).
OVERSAMPLE = 5


def _note_id_of(match: dict) -> str:
    """The vector id is `note_id::chunk_index` for chunked entries; legacy
    entries (single-vector-per-note) use the bare note id with no metadata."""
    metadata = match.get("metadata", {}) or {}
    if metadata.get("note_id"):
        return metadata["note_id"]
    return match.get("id", "")


@router.get("/", response_model=list[SearchResult])
async def search(q: str, top_k: int = 10) -> list[SearchResult]:
    [vector] = embedding_service.embed([q])
    try:
        matches = await vector_store.query(vector, top_k=top_k * OVERSAMPLE)
    except VectorStoreNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    best_per_note: dict[str, dict] = {}
    for m in matches:
        note_id = _note_id_of(m)
        if not note_id:
            continue
        prev = best_per_note.get(note_id)
        if prev is None or float(m.get("score", 0.0)) > float(prev.get("score", 0.0)):
            best_per_note[note_id] = m

    deduped = sorted(
        best_per_note.values(),
        key=lambda m: -float(m.get("score", 0.0)),
    )[:top_k]

    return [
        SearchResult(
            note_id=_note_id_of(m),
            title=(m.get("metadata") or {}).get("title", ""),
            score=float(m.get("score", 0.0)),
        )
        for m in deduped
    ]
