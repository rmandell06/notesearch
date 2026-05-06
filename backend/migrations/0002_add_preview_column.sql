-- Stores a representative chunk picked at upload time, replacing the
-- "first 200 characters" preview that surfaced for long PDFs as
-- whatever happened to be on page 1 (often just a header).
--
-- Idempotent — safe to re-run.

ALTER TABLE notes ADD COLUMN IF NOT EXISTS preview TEXT;
