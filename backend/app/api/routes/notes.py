import io
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.deps import current_user
from app.schemas.note import NoteCreate, NoteResponse
from app.services.embedding import embedding_service
from app.services.storage import storage_service
from app.services.supabase_client import SupabaseNotConfigured, supabase_client
from app.services.vector_store import VectorStoreNotConfigured, vector_store


logger = logging.getLogger(__name__)
router = APIRouter()
TABLE = "notes"

# Word-bounded chunking. ~200 words is roughly ~480 BPE tokens for English on
# this tokenizer, which leaves margin under the encoder's max_seq_len=512 cap.
# 32-word overlap so a sentence isn't sliced in half between chunks.
CHUNK_WORDS = 200
CHUNK_OVERLAP = 32

PREVIEW_LEN = 200


def _config_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=503, detail=str(exc))


async def _supabase():
    try:
        return await supabase_client.client()
    except SupabaseNotConfigured as exc:
        raise _config_error(exc) from exc


def _chunk(text: str, size: int = CHUNK_WORDS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into roughly token-bounded chunks at word boundaries."""
    words = text.split()
    if not words:
        return [""]
    chunks: list[str] = []
    i = 0
    step = max(size - overlap, 1)
    while i < len(words):
        chunks.append(" ".join(words[i : i + size]))
        i += step
    return chunks


def _vector_id(note_id: str, chunk_index: int) -> str:
    return f"{note_id}::{chunk_index}"


def _make_preview(content: str, max_len: int = PREVIEW_LEN) -> str:
    text = content.strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _format_date(ts: str | datetime | None) -> str:
    """`Mar 30, 2026` from an ISO string or datetime; empty string on parse fail."""
    if not ts:
        return ""
    if isinstance(ts, datetime):
        dt = ts
    else:
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except ValueError:
            return str(ts)[:10]
    return f"{_MONTHS[dt.month - 1]} {dt.day}, {dt.year}"


def _build_note_response(row: dict) -> NoteResponse:
    content = row.get("content", "") or ""
    return NoteResponse(
        id=row["id"],
        title=row.get("title", ""),
        content=content,
        body=content,
        preview=_make_preview(content),
        date=_format_date(row.get("created_at")),
        created_at=row.get("created_at") or datetime.utcnow(),
        source=row.get("source", "text"),
    )


def _extract_text(data: bytes, filename: str) -> str:
    """Best-effort text extraction. PDFs via pypdf if available, otherwise
    decode as UTF-8 with errors ignored. Misclassified files just produce
    weak text — never fatal for the upload flow."""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            logger.warning("PDF extraction failed for %s: %s", filename, exc)
    return data.decode("utf-8", errors="ignore")


async def _index_chunks(
    note_id: str,
    title: str,
    content: str,
    user_id: str,
    created_at: str,
    chunks: list[str],
) -> None:
    """Embed each chunk and upsert it into the vector index.

    Failures here shouldn't lose the note — the row is already in Supabase,
    and the user can re-index later. Caller decides whether the note had
    chunks generated."""
    if not chunks:
        return
    try:
        vectors = embedding_service.embed([f"{title}\n{c}" for c in chunks])
        await vector_store.upsert(
            [
                {
                    "id": _vector_id(note_id, idx),
                    "values": vec,
                    "metadata": {
                        "note_id": note_id,
                        "chunk_index": idx,
                        "title": title,
                        "user_id": user_id,
                        "snippet": chunk[:PREVIEW_LEN],
                        "created_at": created_at,
                    },
                }
                for idx, (chunk, vec) in enumerate(zip(chunks, vectors))
            ]
        )
    except VectorStoreNotConfigured:
        pass  # search will be unavailable until creds are set; note still saved


# ── Note: declare /upload before /{note_id} so it doesn't get shadowed ────


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    user_id: str = Depends(current_user),
) -> dict:
    """Multipart upload: file body + optional title. Extracts text (PDF via
    pypdf, plain text otherwise), saves the raw file to storage, creates the
    note row, and indexes chunks."""
    data = await file.read()
    filename = file.filename or "upload"
    storage_key, _ = await storage_service.save(
        data, filename, file.content_type or "application/octet-stream"
    )
    content = _extract_text(data, filename)
    note_title = title or filename

    chunks = _chunk(content)
    client = await _supabase()
    insert_resp = await (
        client.table(TABLE)
        .insert(
            {
                "user_id": user_id,
                "title": note_title,
                "content": content,
                "storage_key": storage_key,
                "source": "upload",
                "chunk_count": len(chunks),
            }
        )
        .execute()
    )
    if not insert_resp.data:
        raise HTTPException(status_code=500, detail="Insert failed")
    row = insert_resp.data[0]

    await _index_chunks(
        note_id=row["id"],
        title=note_title,
        content=content,
        user_id=user_id,
        created_at=row.get("created_at", ""),
        chunks=chunks,
    )

    return {"id": row["id"], "title": note_title, "status": "uploaded"}


@router.post("/", response_model=NoteResponse)
async def create_note(
    note: NoteCreate,
    user_id: str = Depends(current_user),
) -> NoteResponse:
    chunks = _chunk(note.content)

    client = await _supabase()
    insert_resp = await (
        client.table(TABLE)
        .insert(
            {
                "user_id": user_id,
                "title": note.title,
                "content": note.content,
                "source": "text",
                "chunk_count": len(chunks),
            }
        )
        .execute()
    )
    if not insert_resp.data:
        raise HTTPException(status_code=500, detail="Insert failed")
    row = insert_resp.data[0]

    await _index_chunks(
        note_id=row["id"],
        title=note.title,
        content=note.content,
        user_id=user_id,
        created_at=row.get("created_at", ""),
        chunks=chunks,
    )

    return _build_note_response(row)


@router.get("/", response_model=list[NoteResponse])
async def list_notes(
    limit: int = 10,
    user_id: str = Depends(current_user),
) -> list[NoteResponse]:
    client = await _supabase()
    resp = await (
        client.table(TABLE)
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return [_build_note_response(row) for row in (resp.data or [])]


@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(
    note_id: str,
    user_id: str = Depends(current_user),
) -> NoteResponse:
    client = await _supabase()
    resp = await (
        client.table(TABLE)
        .select("*")
        .eq("id", note_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Note not found")
    return _build_note_response(resp.data)


@router.delete("/{note_id}")
async def delete_note(
    note_id: str,
    user_id: str = Depends(current_user),
) -> dict:
    client = await _supabase()
    resp = await (
        client.table(TABLE)
        .delete()
        .eq("id", note_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Note not found")

    deleted = resp.data[0]
    chunk_count = deleted.get("chunk_count") or 0
    if chunk_count > 0:
        ids_to_delete = [_vector_id(note_id, i) for i in range(chunk_count)]
    else:
        ids_to_delete = [note_id]

    storage_key = deleted.get("storage_key")
    if storage_key:
        try:
            await storage_service.delete(storage_key)
        except Exception as exc:
            logger.warning("storage delete failed for %s: %s", storage_key, exc)

    try:
        await vector_store.delete(ids_to_delete)
    except VectorStoreNotConfigured:
        pass

    return {"status": "deleted", "id": note_id}
