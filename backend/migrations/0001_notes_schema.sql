-- Notes table for the FastAPI backend.
-- Run once in the Supabase SQL editor against a fresh project, or apply the
-- ALTERs at the bottom against an existing notes table.

CREATE TABLE IF NOT EXISTS notes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    storage_key TEXT,
    source TEXT NOT NULL DEFAULT 'text',
    chunk_count INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Row-level security so a user can only see their own notes. The auth.uid()
-- function returns the authenticated user's id from the JWT.
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS users_own_notes ON notes;
CREATE POLICY users_own_notes ON notes
    FOR ALL
    USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS notes_user_id_created_at
    ON notes (user_id, created_at DESC);

-- ── If you already have a notes table from before chunking landed: ─────────
-- ALTER TABLE notes ADD COLUMN IF NOT EXISTS chunk_count INTEGER NOT NULL DEFAULT 1;
