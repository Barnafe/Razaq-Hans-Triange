-- Migration: adds the patient-submit -> admin-review -> doctor-attend
-- workflow columns to an ALREADY-EXISTING database (yours), without
-- dropping or losing any data you've already created (e.g. your
-- PT-1EE4E78D test assessment).
--
-- schema_postgres.sql (the full schema) has also been updated to match,
-- for anyone setting up the database from scratch in the future -- this
-- file is only for upgrading a database that already has the OLD table
-- structure, like yours does right now.
--
-- Safe to run more than once (every statement below is idempotent).
--
-- Run it with:
--   psql -U postgres -d hans_triage -f backend/app/db/migration_review_workflow.sql

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_available BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE patients
    ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(user_id);

ALTER TABLE triage_decisions
    ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'finalized',
    ADD COLUMN IF NOT EXISTS assigned_doctor_id INTEGER REFERENCES users(user_id),
    ADD COLUMN IF NOT EXISTS reviewed_by INTEGER REFERENCES users(user_id),
    ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

-- Add the CHECK constraint separately -- ADD COLUMN doesn't support
-- attaching one inline with IF NOT EXISTS, so guard it manually.
DO $$
BEGIN
    ALTER TABLE triage_decisions
        ADD CONSTRAINT triage_decisions_status_check
        CHECK (status IN ('pending_review', 'approved', 'rejected', 'attended', 'finalized'));
EXCEPTION
    WHEN duplicate_object THEN
        NULL; -- constraint already exists from a previous run, fine
END $$;

CREATE INDEX IF NOT EXISTS idx_triage_status ON triage_decisions(status);
CREATE INDEX IF NOT EXISTS idx_triage_assigned_doctor ON triage_decisions(assigned_doctor_id);

-- Sanity check: confirms every existing row (your earlier test data)
-- correctly defaulted to 'finalized' and nothing was lost.
SELECT decision_id, status FROM triage_decisions ORDER BY decision_id;
