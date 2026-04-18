from pydantic import BaseModel


class SearchQuery(BaseModel):
    query: str
    top_k: int = 10


class SearchResult(BaseModel):
    note_id: str
    title: str
    score: float
