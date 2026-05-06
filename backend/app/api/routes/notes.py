import io
import logging
import math
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.deps import current_user
from app.schemas.note import NoteCreate, NoteResponse, NoteUpdate
from app.services.embedding import embedding_service
from app.services.storage import storage_service
from app.services.supabase_client import SupabaseNotConfigured, supabase_client
from app.services.vector_store import VectorStoreNotConfigured, vector_store


logger = logging.getLogger(__name__)
router = APIRouter()
TABLE = "notes"

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


def _truncate(text: str, max_len: int = PREVIEW_LEN) -> str:
    text = (text or "").strip()
    return text[:max_len] + ("…" if len(text) > max_len else "")


def _cosine(a: list[float], b: list[float]) -> float:
    """Manual cosine similarity. Vectors aren't pre-normalized."""
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _format_date(ts: str | datetime | None) -> str:
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
    """Build the response shape the frontend cards consume.

    Prefers the `preview` column (stored at upload time as the chunk most
    similar to the title) over a naive `content[:200]` slice. Falls back
    to the slice for legacy rows uploaded before the preview column existed.
    """
    content = row.get("content", "") or ""
    stored_preview = (row.get("preview") or "").strip()
    preview = stored_preview if stored_preview else _truncate(content)
    return NoteResponse(
        id=row["id"],
        title=row.get("title", ""),
        content=content,
        body=content,
        preview=preview,
        date=_format_date(row.get("created_at")),
        created_at=row.get("created_at") or datetime.utcnow(),
        source=row.get("source", "text"),
    )


def _extract_text(data: bytes, filename: str) -> str:
    """Extract human-readable text from an uploaded file."""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        try:
            import pdfplumber

            with pdfplumber.open(io.BytesIO(data)) as pdf:
                pages = [p.extract_text() or "" for p in pdf.pages]
            text = "\n\n".join(pages).strip()
        except Exception as exc:
            logger.warning("PDF extraction failed for %s: %s", filename, exc)
            text = ""
        return text.replace("\x00", "")

    return data.decode("utf-8", errors="ignore").replace("\x00", "")


def _embed_for_indexing(
    title: str, chunks: list[str]
) -> tuple[str, list[list[float]] | None]:
    """Embed everything needed to index a note + pick its preview.

    Returns (preview_text, search_vectors). search_vectors is a list with
    one entry per chunk (the title-prefixed embedding stored in Vectorize),
    or None if embedding failed entirely (in which case the note is still
    saved, just not searchable).

    Strategy:
      - 1 chunk: the chunk IS the representative; just embed the search
        vector and use the chunk text as preview.
      - N > 1 chunks: batch [title, *chunks, *(title+chunk)] in a single
        embed call, then pick max cosine(title, chunk_alone) as preview.
    """
    if not chunks:
        return "", None

    if len(chunks) == 1:
        try:
            search_vec = embedding_service.embed([f"{title}\n{chunks[0]}"])[0]
        except Exception as exc:  # pragma: no cover  # best-effort
            logger.warning("embedding failed: %s", exc)
            return _truncate(chunks[0]), None
        return _truncate(chunks[0]), [search_vec]

    n = len(chunks)
    batch = [title] + chunks + [f"{title}\n{c}" for c in chunks]
    try:
        all_vecs = embedding_service.embed(batch)
    except Exception as exc:  # pragma: no cover
        logger.warning("embedding failed: %s", exc)
        return _truncate(chunks[0]), None

    title_vec = all_vecs[0]
    chunk_vecs = all_vecs[1 : 1 + n]
    search_vecs = all_vecs[1 + n :]

    best_idx = max(range(n), key=lambda i: _cosine(title_vec, chunk_vecs[i]))
    return _truncate(chunks[best_idx]), search_vecs


async def _upsert_chunks(
    note_id: str,
    title: str,
    user_id: str,
    created_at: str,
    chunks: list[str],
    search_vecs: list[list[float]],
) -> None:
    """Best-effort upsert of chunk vectors into Vectorize."""
    try:
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
                        "snippet": _truncate(chunk),
                        "created_at": created_at,
                    },
                }
                for idx, (chunk, vec) in enumerate(zip(chunks, search_vecs))
            ]
        )
    except VectorStoreNotConfigured:
        pass


# ── routes ────────────────────────────────────────────────────────────────


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    user_id: str = Depends(current_user),
) -> dict:
    data = await file.read()
    filename = file.filename or "upload"
    storage_key, _ = await storage_service.save(
        data, filename, file.content_type or "application/octet-stream"
    )
    content = _extract_text(data, filename)
    note_title = title or filename

    chunks = _chunk(content)
    preview, search_vecs = _embed_for_indexing(note_title, chunks)

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
                "preview": preview,
            }
        )
        .execute()
    )
    if not insert_resp.data:
        raise HTTPException(status_code=500, detail="Insert failed")
    row = insert_resp.data[0]

    if search_vecs is not None:
        await _upsert_chunks(
            row["id"], note_title, user_id, row.get("created_at", ""), chunks, search_vecs
        )

    return {"id": row["id"], "title": note_title, "status": "uploaded"}


@router.post("/", response_model=NoteResponse)
async def create_note(
    note: NoteCreate,
    user_id: str = Depends(current_user),
) -> NoteResponse:
    chunks = _chunk(note.content)
    preview, search_vecs = _embed_for_indexing(note.title, chunks)

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
                "preview": preview,
            }
        )
        .execute()
    )
    if not insert_resp.data:
        raise HTTPException(status_code=500, detail="Insert failed")
    row = insert_resp.data[0]

    if search_vecs is not None:
        await _upsert_chunks(
            row["id"], note.title, user_id, row.get("created_at", ""), chunks, search_vecs
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


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(
    note_id: str,
    update: NoteUpdate,
    user_id: str = Depends(current_user),
) -> NoteResponse:
    """Partially update a note. Currently used for renames (title only) and
    free-text edits (content). Title-only changes do not re-index vectors —
    the existing chunk vectors keep their old title in metadata until the
    note is re-uploaded. Acceptable trade-off for a demo; renaming hundreds
    of notes a day would warrant a background re-index queue."""
    fields = update.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    client = await _supabase()
    resp = await (
        client.table(TABLE)
        .update(fields)
        .eq("id", note_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Note not found")
    return _build_note_response(resp.data[0])


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
