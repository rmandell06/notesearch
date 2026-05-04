from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import current_user
from app.schemas.note import NoteCreate, NoteResponse
from app.services.embedding import embedding_service
from app.services.supabase_client import SupabaseNotConfigured, supabase_client
from app.services.vector_store import VectorStoreNotConfigured, vector_store


router = APIRouter()
TABLE = "notes"


def _config_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=503, detail=str(exc))


async def _supabase():
    try:
        return await supabase_client.client()
    except SupabaseNotConfigured as exc:
        raise _config_error(exc) from exc


@router.post("/", response_model=NoteResponse)
async def upload_note(
    note: NoteCreate,
    user_id: str = Depends(current_user),
) -> NoteResponse:
    client = await _supabase()
    insert_resp = await (
        client.table(TABLE)
        .insert(
            {
                "user_id": user_id,
                "title": note.title,
                "content": note.content,
                "source": "text",
            }
        )
        .execute()
    )
    if not insert_resp.data:
        raise HTTPException(status_code=500, detail="Insert failed")
    row = insert_resp.data[0]

    # Embed and upsert into the vector index. Failures here shouldn't lose
    # the note — log via the exception and fall through; user can re-index later.
    try:
        [vector] = embedding_service.embed([f"{note.title}\n{note.content}"])
        await vector_store.upsert(
            [
                {
                    "id": row["id"],
                    "values": vector,
                    "metadata": {"title": note.title, "user_id": user_id},
                }
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

    try:
        await vector_store.delete([note_id])
    except VectorStoreNotConfigured:
        pass  # delete is best-effort; vector left orphaned if index unavailable

    return {"status": "deleted", "id": note_id}
