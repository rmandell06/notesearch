import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.services.supabase_client import supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


def _format_date(ts: str) -> str:
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        return f"{months[dt.month - 1]} {dt.day}, {dt.year}"
    except Exception:
        return ts[:10]


def _make_preview(content: str, max_len: int = 200) -> str:
    text = content.strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


@router.get("/")
async def search(
    q: str,
    top_k: int = 10,
    user: dict = Depends(get_current_user),
) -> list:
    if not q.strip():
        return []

    user_id: str = user["id"]
    notes = supabase_client.search_notes(user_id, q, limit=top_k)

    results = []
    for note in notes:
        content = note.get("content", "")
        results.append({
            "id": note["id"],
            "title": note["title"],
            "preview": _make_preview(content),
            "body": content,
            "date": _format_date(note.get("created_at", "")),
            "tags": [],
            "source": note.get("source", "text"),
            "relevance": note.get("relevance", 0.0),
        })

    return results
