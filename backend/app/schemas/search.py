from pydantic import BaseModel


class SearchQuery(BaseModel):
    query: str
    top_k: int = 10


class SearchResult(BaseModel):
    """Search-result shape mirrors the listing shape so the frontend's
    NoteCard can render either without branching. `score` and `relevance`
    hold the same value (0-1 cosine similarity) — the duplicate field is
    kept to keep both names available to clients."""

    id: str
    note_id: str
    title: str
    preview: str
    date: str
    score: float
    relevance: float
