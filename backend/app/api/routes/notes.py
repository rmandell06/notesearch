from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def upload_note() -> dict:
    raise NotImplementedError


@router.get("/")
async def list_notes() -> list:
    raise NotImplementedError


@router.get("/{note_id}")
async def get_note(note_id: str) -> dict:
    raise NotImplementedError


@router.delete("/{note_id}")
async def delete_note(note_id: str) -> dict:
    raise NotImplementedError
