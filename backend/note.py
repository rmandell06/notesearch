import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    String, Text, DateTime, Integer, Boolean,
    ForeignKey, UniqueConstraint, Index, Enum as SAEnum,
    JSON, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

# JSON works across dialects; Alembic migration uses JSONB for Postgres
JsonType = JSON

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SourceType(str, enum.Enum):
    FILE = "file"
    BROWSER = "browser"
    VOICE = "voice"
    MANUAL = "manual"


class EmbeddingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class NoteStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


# ── Association table: notes ↔ tags ─────────────────────────────────────────

class NoteTag(Base):
    __tablename__ = "note_tags"

    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )


# ── Tag ──────────────────────────────────────────────────────────────────────

class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("name", name="uq_tags_name"),
        Index("ix_tags_name_lower", func.lower(func.cast("name", String))),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(7))  # hex #rrggbb
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    notes: Mapped[list["Note"]] = relationship(
        "Note", secondary="note_tags", back_populates="tags"
    )

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name!r}>"


# ── Note ─────────────────────────────────────────────────────────────────────

class Note(Base):
    __tablename__ = "notes"
    __table_args__ = (
        Index("ix_notes_created_at", "created_at"),
        Index("ix_notes_source_type", "source_type"),
        Index("ix_notes_status", "status"),
        Index("ix_notes_embedding_status", "embedding_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )

    # Content
    title: Mapped[Optional[str]] = mapped_column(String(500))
    raw_content: Mapped[Optional[str]] = mapped_column(Text)
    processed_content: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(String(1000))

    # Source
    source_type: Mapped[SourceType] = mapped_column(
        SAEnum(SourceType, name="source_type_enum"), nullable=False
    )
    source_url: Mapped[Optional[str]] = mapped_column(String(2048))
    source_metadata: Mapped[Optional[dict]] = mapped_column(JsonType())

    # State
    status: Mapped[NoteStatus] = mapped_column(
        SAEnum(NoteStatus, name="note_status_enum"),
        default=NoteStatus.ACTIVE,
        server_default="active",
    )
    embedding_status: Mapped[EmbeddingStatus] = mapped_column(
        SAEnum(EmbeddingStatus, name="embedding_status_enum"),
        default=EmbeddingStatus.PENDING,
        server_default="pending",
    )
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    word_count: Mapped[Optional[int]] = mapped_column(Integer)
    char_count: Mapped[Optional[int]] = mapped_column(Integer)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, server_default=func.now()
    )
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    tags: Mapped[list[Tag]] = relationship(
        "Tag", secondary="note_tags", back_populates="notes", lazy="selectin"
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment", back_populates="note", cascade="all, delete-orphan", lazy="selectin"
    )
    chunks: Mapped[list["NoteChunk"]] = relationship(
        "NoteChunk", back_populates="note", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Note id={self.id} title={self.title!r} source={self.source_type}>"

    @property
    def is_indexed(self) -> bool:
        return self.embedding_status == EmbeddingStatus.COMPLETE


# ── Attachment ────────────────────────────────────────────────────────────────

class Attachment(Base):
    __tablename__ = "attachments"
    __table_args__ = (
        Index("ix_attachments_note_id", "note_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    storage_backend: Mapped[str] = mapped_column(String(20), default="local")
    checksum_sha256: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    note: Mapped["Note"] = relationship("Note", back_populates="attachments")

    def __repr__(self) -> str:
        return f"<Attachment id={self.id} filename={self.original_filename!r}>"


# ── NoteChunk ─────────────────────────────────────────────────────────────────

class NoteChunk(Base):
    """Processed text segments used for embedding and retrieval."""
    __tablename__ = "note_chunks"
    __table_args__ = (
        Index("ix_note_chunks_note_id", "note_id"),
        Index("ix_note_chunks_embedding_status", "embedding_status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[Optional[int]] = mapped_column(Integer)
    char_start: Mapped[Optional[int]] = mapped_column(Integer)
    char_end: Mapped[Optional[int]] = mapped_column(Integer)

    embedding_status: Mapped[EmbeddingStatus] = mapped_column(
        SAEnum(EmbeddingStatus, name="embedding_status_enum"),
        default=EmbeddingStatus.PENDING,
    )
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100))
    embedded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    note: Mapped["Note"] = relationship("Note", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<NoteChunk id={self.id} note_id={self.note_id} idx={self.chunk_index}>"
