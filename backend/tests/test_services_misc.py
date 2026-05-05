"""Lightweight smoke tests for service modules with little inherent logic.

Goal: keep the line-coverage bar honest without paying for full unit coverage
on third-party-shaped wrappers (Supabase, AWS Transcribe, file storage). Each
test asserts the singleton imports and exposes its expected surface; deeper
behavioral testing happens in the route-level tests where these services are
exercised end-to-end.
"""
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.note import Note
from app.schemas.voice import TranscriptionJob
from app.services.connections import connections_service
from app.services.supabase_client import (
    SupabaseClient,
    SupabaseNotConfigured,
    supabase_client,
)
from app.services.transcription import transcription_service


def test_supabase_client_raises_when_unconfigured() -> None:
    sc = SupabaseClient()
    sc.url = ""
    sc.key = ""
    with pytest.raises(SupabaseNotConfigured):
        # Calling .client() inside an event loop is fine; we only need the
        # config check, which runs before any awaits.
        import asyncio

        asyncio.get_event_loop().run_until_complete(sc.client())


def test_supabase_client_singleton_exposes_url_and_key_attrs() -> None:
    assert hasattr(supabase_client, "url")
    assert hasattr(supabase_client, "key")


def test_transcription_service_exposes_submit() -> None:
    assert callable(transcription_service.submit)
    assert callable(transcription_service.poll)


@pytest.mark.asyncio
async def test_connections_returns_empty_for_no_notes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty-corpus path keeps the service safe to call before the user has
    written any notes."""
    fake = MagicMock()
    chain = MagicMock()
    for m in ("select", "eq", "limit"):
        getattr(chain, m).return_value = chain
    chain.execute = AsyncMock(return_value=SimpleNamespace(data=[]))
    fake.table.return_value = chain
    monkeypatch.setattr(supabase_client, "client", AsyncMock(return_value=fake))

    result = await connections_service.build_graph("u-1")
    assert result == {"nodes": [], "links": []}


@pytest.mark.asyncio
async def test_connections_builds_links_above_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        {"id": "00000000-0000-0000-0000-000000000001", "title": "A", "content": "the cat sat on the mat"},
        {"id": "00000000-0000-0000-0000-000000000002", "title": "B", "content": "a cat is sitting on a mat"},
        {"id": "00000000-0000-0000-0000-000000000003", "title": "C", "content": "completely different topic about astronomy"},
    ]
    fake = MagicMock()
    chain = MagicMock()
    for m in ("select", "eq", "limit"):
        getattr(chain, m).return_value = chain
    chain.execute = AsyncMock(return_value=SimpleNamespace(data=rows))
    fake.table.return_value = chain
    monkeypatch.setattr(supabase_client, "client", AsyncMock(return_value=fake))

    g = await connections_service.build_graph("u-1", threshold=0.1)
    assert len(g["nodes"]) == 3
    # A↔B should be linked (heavy word overlap), neither linked to C.
    linked = {(l["source"], l["target"]) for l in g["links"]}
    assert (rows[0]["id"], rows[1]["id"]) in linked
    assert all(rows[2]["id"] not in pair for pair in linked)


def test_note_dataclass_holds_fields() -> None:
    n = Note(
        id="n-1",
        user_id="u-1",
        title="t",
        content="c",
        storage_key="sk",
        source="text",
        created_at=datetime.utcnow(),
    )
    assert n.id == "n-1"
    assert n.source == "text"


def test_voice_schema_round_trips() -> None:
    job = TranscriptionJob(job_id="j-1", status="pending")
    assert job.transcript is None
    assert TranscriptionJob(**job.model_dump()).job_id == "j-1"
