from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def upload_voice() -> dict:
    raise NotImplementedError


@router.get("/{job_id}")
async def get_transcription_status(job_id: str) -> dict:
    raise NotImplementedError
