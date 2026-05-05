from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import current_user
from app.schemas.note import NoteCreate, NoteResponse
from app.services.embedding import embedding_service
from app.services.supabase_client import SupabaseNotConfigured, supabase_client
from app.services.vector_store import VectorStoreNotConfigured, vector_store


router = APIRouter()
TABLE = "notes"

# Word-bounded chunking. ~200 words is roughly ~480 BPE tokens for English on
# this tokenizer, which leaves margin under the encoder's max_seq_len=512 cap.
# 32-word overlap so a sentence isn't sliced in half between chunks.
CHUNK_WORDS = 200
CHUNK_OVERLAP = 32


def _config_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=503, detail=str(exc))


async def _supabase():
    try:
        return await supabase_client.client()
    except SupabaseNotConfigured as exc:
        raise _config_error(exc) from exc


def _chunk(text: str, size: int = CHUNK_WORDS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into roughly token-bounded chunks at word boundaries.

    Word-count is an approximation of BPE tokens; the embedding service still
    truncates anything over max_seq_len, so going slightly over is safe.
    """
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


@router.post("/", response_model=NoteResponse)
async def upload_note(
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

    # Embed each chunk and upsert one vector per chunk. Each chunk gets a
    # composite id (note_id::chunk_index) and metadata pointing back to its
    # parent note so /search can collapse hits back to a single result.
    try:
        vectors = embedding_service.embed(
            [f"{note.title}\n{chunk}" for chunk in chunks]
        )
        await vector_store.upsert(
            [
                {
                    "id": _vector_id(row["id"], idx),
                    "values": vec,
                    "metadata": {
                        "note_id": row["id"],
                        "chunk_index": idx,
                        "title": note.title,
                        "user_id": user_id,
                        "snippet": chunk[:200],
                    },
                }
                for idx, (chunk, vec) in enumerate(zip(chunks, vectors))
            ]
        )
    except VectorStoreNotConfigured:
        pass  # search will be unavailable until creds are set; note still saved

    return NoteResponse(**row)


@router.get("/", response_model=list[NoteResponse])
async def list_notes(user_id: str = Depends(current_user)) -> list[NoteResponse]:
    client = await _supabase()
    resp = await (
        client.table(TABLE)
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [NoteResponse(**row) for row in (resp.data or [])]


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
    return NoteResponse(**resp.data)


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

    # The deleted row tells us how many chunks to drop. Older rows without
    # chunk_count default to 1 vector under the bare note_id (legacy format).
    deleted = resp.data[0]
    chunk_count = deleted.get("chunk_count") or 0
    if chunk_count > 0:
        ids_to_delete = [_vector_id(note_id, i) for i in range(chunk_count)]
    else:
        ids_to_delete = [note_id]

    try:
        await vector_store.delete(ids_to_delete)
    except VectorStoreNotConfigured:
        pass  # delete is best-effort; vectors orphaned if index unavailable

    return {"status": "deleted", "id": note_id}
