from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/")
async def upload_voice() -> dict:
    return JSONResponse(
        status_code=501,
        content={"detail": "Voice transcription not yet implemented"},
    )


@router.get("/{job_id}")
async def get_transcription_status(job_id: str) -> dict:
    return JSONResponse(
        status_code=501,
        content={"detail": "Voice transcription not yet implemented"},
    )
