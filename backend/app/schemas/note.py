from datetime import datetime

from pydantic import BaseModel


class NoteCreate(BaseModel):
    title: str
    content: str


class NoteResponse(BaseModel):
    """Returned by /notes/* endpoints. `preview` and `date` are derived
    server-side so the frontend can render note cards without re-deriving
    formatting on every list rerender."""

    id: str
    title: str
    content: str
    preview: str
    body: str
    date: str
    created_at: datetime
    source: str
