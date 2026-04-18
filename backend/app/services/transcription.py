from app.services.storage import storage_service


class TranscriptionService:
    """S3 upload + AWS Transcribe async job polling."""

    async def submit(self, audio_bytes: bytes, filename: str, mime_type: str) -> str:
        storage_key, _ = await storage_service.save(audio_bytes, filename, mime_type)
        return storage_key

    async def poll(self, job_id: str) -> dict:
        raise NotImplementedError


transcription_service = TranscriptionService()
