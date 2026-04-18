from pydantic import BaseModel


class TranscriptionJob(BaseModel):
    job_id: str
    status: str
    transcript: str | None = None
