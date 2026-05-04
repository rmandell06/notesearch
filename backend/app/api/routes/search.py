from fastapi import APIRouter, HTTPException

from app.schemas.search import SearchResult
from app.services.embedding import embedding_service
from app.services.vector_store import VectorStoreNotConfigured, vector_store


router = APIRouter()


@router.get("/", response_model=list[SearchResult])
async def search(q: str, top_k: int = 10) -> list[SearchResult]:
    [vector] = embedding_service.embed([q])
    try:
        matches = await vector_store.query(vector, top_k=top_k)
    except VectorStoreNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return [
        SearchResult(
            note_id=m.get("id", ""),
            title=m.get("metadata", {}).get("title", ""),
            score=float(m.get("score", 0.0)),
        )
        for m in matches
    ]
