from datetime import datetime
from pydantic import BaseModel


class NoteCreate(BaseModel):
    title: str
    content: str


class NoteResponse(BaseModel):
    id: str
    title: str
    content: str
    created_at: datetime
    source: str
