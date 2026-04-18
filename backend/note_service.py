import uuid
import asyncio
from typing import Optional

import httpx
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import (
    NoteNotFoundError, TagNotFoundError, FileTooLargeError,
    UnsupportedFileTypeError, StorageError,
)
from app.models.note import Note, Attachment, NoteChunk, EmbeddingStatus, SourceType
from app.repositories.note_repository import NoteRepository
from app.repositories.tag_repository import TagRepository
from app.schemas.note import NoteCreate, NoteUpdate, NoteFilter, PaginationParams, EmbeddingStatusUpdate
from app.services.processor import content_processor
from app.services.storage import storage_service


class NoteService:
    """
    Orchestrates the complete note lifecycle:
    create → process → store → dispatch embedding job.
    """

    def __init__(self, note_repo: NoteRepository, tag_repo: TagRepository):
        self.note_repo = note_repo
        self.tag_repo = tag_repo

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_note(
        self,
        data: NoteCreate,
        user_id: Optional[uuid.UUID] = None,
    ) -> Note:
        tags = await self._resolve_tags(data.tag_ids)

        processed = None
        if data.raw_content:
            processed = content_processor.process(data.raw_content, data.source_type.value)

        note = Note(
            user_id=user_id,
            title=data.title or self._infer_title(data.raw_content),
            raw_content=data.raw_content,
            processed_content=processed.cleaned if processed else None,
            summary=processed.summary if processed else None,
            source_type=data.source_type,
            source_url=data.source_url,
            source_metadata=data.source_metadata,
            is_pinned=data.is_pinned,
            word_count=processed.word_count if processed else None,
            char_count=processed.char_count if processed else None,
            embedding_status=(
                EmbeddingStatus.PENDING if data.raw_content else EmbeddingStatus.FAILED
            ),
        )
        note.tags = tags
        note = await self.note_repo.create(note)

        # Store chunks for embedding pipeline
        if processed and processed.chunks:
            chunks = [
                NoteChunk(
                    note_id=note.id,
                    chunk_index=c.index,
                    content=c.content,
                    token_count=c.token_estimate,
                    char_start=c.char_start,
                    char_end=c.char_end,
                )
                for c in processed.chunks
            ]
            await self.note_repo.replace_chunks(note.id, chunks)

        # Fire-and-forget: notify embedding worker
        if settings.EMBEDDING_QUEUE_ENABLED and data.raw_content:
            asyncio.create_task(self._dispatch_embedding_job(note.id))

        return note

    async def create_from_file(
        self,
        file: UploadFile,
        source_type: SourceType,
        title: Optional[str] = None,
        tag_ids: Optional[list[uuid.UUID]] = None,
        user_id: Optional[uuid.UUID] = None,
    ) -> Note:
        file_bytes = await file.read()

        # Validate size
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            raise FileTooLargeError(size_mb, settings.MAX_FILE_SIZE_MB)

        # Validate MIME type
        mime_type = file.content_type or "application/octet-stream"
        if mime_type not in settings.ALLOWED_MIME_TYPES:
            raise UnsupportedFileTypeError(mime_type)

        # Extract text content
        raw_content = await self._extract_text(file_bytes, mime_type, file.filename)

        # Persist file
        storage_key, checksum = await storage_service.save(
            file_bytes, file.filename, mime_type
        )

        # Create note
        create_data = NoteCreate(
            title=title or file.filename,
            raw_content=raw_content,
            source_type=source_type,
            tag_ids=tag_ids or [],
        )
        note = await self.create_note(create_data, user_id)

        # Attach the file record
        attachment = Attachment(
            note_id=note.id,
            filename=storage_key,
            original_filename=file.filename,
            mime_type=mime_type,
            size_bytes=len(file_bytes),
            storage_key=storage_key,
            storage_backend=settings.STORAGE_BACKEND,
            checksum_sha256=checksum,
        )
        await self.note_repo.add_attachment(attachment)

        return note

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_note(
        self, note_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> Note:
        if user_id:
            note = await self.note_repo.get_by_id_for_user(note_id, user_id)
        else:
            note = await self.note_repo.get_by_id(note_id)
        if not note:
            raise NoteNotFoundError(str(note_id))
        return note

    async def list_notes(
        self,
        filters: NoteFilter,
        pagination: PaginationParams,
        user_id: Optional[uuid.UUID] = None,
    ) -> tuple[list[Note], int]:
        return await self.note_repo.list(filters, pagination, user_id)

    # ── Update ─────────────────────────────────────────────────────────────────

    async def update_note(
        self,
        note_id: uuid.UUID,
        data: NoteUpdate,
        user_id: Optional[uuid.UUID] = None,
    ) -> Note:
        note = await self.get_note(note_id, user_id)

        content_changed = False

        if data.title is not None:
            note.title = data.title
        if data.raw_content is not None and data.raw_content != note.raw_content:
            note.raw_content = data.raw_content
            processed = content_processor.process(data.raw_content, note.source_type.value)
            note.processed_content = processed.cleaned
            note.summary = processed.summary
            note.word_count = processed.word_count
            note.char_count = processed.char_count
            note.embedding_status = EmbeddingStatus.PENDING
            content_changed = True

            chunks = [
                NoteChunk(
                    note_id=note.id,
                    chunk_index=c.index,
                    content=c.content,
                    token_count=c.token_estimate,
                    char_start=c.char_start,
                    char_end=c.char_end,
                )
                for c in processed.chunks
            ]
            await self.note_repo.replace_chunks(note.id, chunks)

        if data.source_url is not None:
            note.source_url = data.source_url
        if data.source_metadata is not None:
            note.source_metadata = data.source_metadata
        if data.is_pinned is not None:
            note.is_pinned = data.is_pinned
        if data.status is not None:
            note.status = data.status
        if data.tag_ids is not None:
            tags = await self._resolve_tags(data.tag_ids)
            await self.note_repo.set_tags(note, tags)

        note = await self.note_repo.update(note)

        if content_changed and settings.EMBEDDING_QUEUE_ENABLED:
            asyncio.create_task(self._dispatch_embedding_job(note.id))

        return note

    # ── Archive / Delete ───────────────────────────────────────────────────────

    async def archive_note(self, note_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Note:
        note = await self.get_note(note_id, user_id)
        return await self.note_repo.archive(note)

    async def restore_note(self, note_id: uuid.UUID, user_id: Optional[uuid.UUID] = None) -> Note:
        note = await self.get_note(note_id, user_id)
        return await self.note_repo.restore(note)

    async def delete_note(
        self,
        note_id: uuid.UUID,
        hard: bool = False,
        user_id: Optional[uuid.UUID] = None,
    ) -> None:
        note = await self.get_note(note_id, user_id)

        # Clean up stored files
        for attachment in note.attachments:
            try:
                await storage_service.delete(attachment.storage_key)
            except StorageError:
                pass  # Log but don't block deletion

        if hard:
            await self.note_repo.hard_delete(note)
        else:
            await self.note_repo.soft_delete(note)

    # ── Attachments ────────────────────────────────────────────────────────────

    async def get_attachment_bytes(
        self, note_id: uuid.UUID, attachment_id: uuid.UUID
    ) -> tuple[bytes, Attachment]:
        note = await self.get_note(note_id)
        attachment = await self.note_repo.get_attachment(attachment_id)
        if not attachment or attachment.note_id != note.id:
            raise NoteNotFoundError(str(attachment_id))
        data = await storage_service.read(attachment.storage_key)
        return data, attachment

    async def delete_attachment(
        self, note_id: uuid.UUID, attachment_id: uuid.UUID
    ) -> None:
        note = await self.get_note(note_id)
        attachment = await self.note_repo.get_attachment(attachment_id)
        if not attachment or attachment.note_id != note.id:
            raise NoteNotFoundError(str(attachment_id))
        await storage_service.delete(attachment.storage_key)
        await self.note_repo.delete_attachment(attachment)

    # ── Embedding status (called by embedding worker) ─────────────────────────

    async def handle_embedding_status_update(self, update: EmbeddingStatusUpdate) -> None:
        await self.note_repo.update_embedding_status(update.note_id, update.status)

    # ── Chunks ─────────────────────────────────────────────────────────────────

    async def get_chunks(self, note_id: uuid.UUID) -> list[NoteChunk]:
        await self.get_note(note_id)  # ensures note exists
        return await self.note_repo.get_chunks(note_id)

    # ── Stats ──────────────────────────────────────────────────────────────────

    async def get_stats(self, user_id: Optional[uuid.UUID] = None) -> dict:
        by_source = await self.note_repo.count_by_source_type(user_id)
        pending_embeddings = await self.note_repo.count_pending_embeddings()
        return {
            "by_source_type": {k.value: v for k, v in by_source.items()},
            "total": sum(by_source.values()),
            "pending_embeddings": pending_embeddings,
        }

    # ── Internal helpers ───────────────────────────────────────────────────────

    async def _resolve_tags(self, tag_ids: list[uuid.UUID]) -> list:
        if not tag_ids:
            return []
        tags = await self.tag_repo.get_by_ids(tag_ids)
        found_ids = {t.id for t in tags}
        missing = [tid for tid in tag_ids if tid not in found_ids]
        if missing:
            raise TagNotFoundError(str(missing[0]))
        return tags

    async def _dispatch_embedding_job(self, note_id: uuid.UUID) -> None:
        if not settings.EMBEDDING_WORKER_URL:
            return
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{settings.EMBEDDING_WORKER_URL}/embed",
                    json={"note_id": str(note_id)},
                )
        except Exception:
            pass  # Worker will pick it up via polling fallback

    async def _extract_text(
        self, file_bytes: bytes, mime_type: str, filename: str
    ) -> Optional[str]:
        """Best-effort text extraction from common file types."""
        if mime_type == "text/plain" or mime_type == "text/markdown":
            return file_bytes.decode("utf-8", errors="replace")

        if mime_type == "text/html":
            text = file_bytes.decode("utf-8", errors="replace")
            from app.services.processor import ContentProcessor
            return ContentProcessor()._strip_html(text)

        if mime_type == "application/pdf":
            return await self._extract_pdf_text(file_bytes)

        # Voice memos: transcription handled by a separate worker
        if mime_type.startswith("audio/"):
            return None

        # DOCX and other formats: return None, processing deferred
        return None

    async def _extract_pdf_text(self, data: bytes) -> Optional[str]:
        try:
            import io
            import asyncio
            import pypdf

            def _extract():
                reader = pypdf.PdfReader(io.BytesIO(data))
                return "\n\n".join(
                    page.extract_text() or "" for page in reader.pages
                )

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _extract)
        except Exception:
            return None

    def _infer_title(self, content: Optional[str]) -> Optional[str]:
        if not content:
            return None
        first_line = content.strip().split("\n")[0].strip()
        # Strip markdown heading syntax
        first_line = first_line.lstrip("# ").strip()
        return first_line[:200] if first_line else None
