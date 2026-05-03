import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from app.api.deps import get_current_user
from app.services.supabase_client import supabase_client
from app.services.storage import storage_service

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


def _note_to_response(note: dict) -> dict:
    content = note.get("content", "")
    return {
        "id": note["id"],
        "title": note["title"],
        "preview": _make_preview(content),
        "body": content,
        "date": _format_date(note.get("created_at", "")),
        "tags": [],
        "source": note.get("source", "text"),
        "created_at": note.get("created_at", ""),
    }


def _extract_text(data: bytes, filename: str) -> str:
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        try:
            import io
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            logger.warning("PDF extraction failed for %s: %s", filename, e)
    return data.decode("utf-8", errors="ignore")


# /notes/upload must be defined before /{note_id} to avoid route shadowing
@router.post("/upload")
async def upload_note(
    file: UploadFile = File(...),
    title: str = Form(default=None),
    user: dict = Depends(get_current_user),
) -> dict:
    user_id: str = user["id"]
    data = await file.read()
    filename = file.filename or "upload"

    storage_key, _ = await storage_service.save(
        data, filename, file.content_type or "text/plain"
    )
    content = _extract_text(data, filename)
    note_title = title or filename

    note_id = supabase_client.create_note(user_id, note_title, content, storage_key, "upload")
    return {"id": note_id, "title": note_title, "status": "uploaded"}


@router.post("/")
async def create_note(
    title: str = Form(...),
    content: str = Form(default=""),
    user: dict = Depends(get_current_user),
) -> dict:
    user_id: str = user["id"]
    note_id = supabase_client.create_note(user_id, title, content, None, "text")
    return {"id": note_id, "title": title, "status": "created"}


@router.get("/")
async def list_notes(
    limit: int = 10,
    user: dict = Depends(get_current_user),
) -> list:
    user_id: str = user["id"]
    notes = supabase_client.list_notes(user_id, limit=limit)
    return [_note_to_response(n) for n in notes]


@router.get("/{note_id}")
async def get_note(
    note_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    user_id: str = user["id"]
    note = supabase_client.get_note(note_id, user_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return _note_to_response(note)


@router.delete("/{note_id}")
async def delete_note(
    note_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    user_id: str = user["id"]
    note = supabase_client.get_note(note_id, user_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    supabase_client.delete_note(note_id, user_id)

    if note.get("storage_key"):
        try:
            await storage_service.delete(note["storage_key"])
        except Exception as e:
            logger.warning("Storage delete failed for %s: %s", note["storage_key"], e)

    return {"deleted": True}
