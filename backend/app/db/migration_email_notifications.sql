-- Migration: adds email + password-reset support to an ALREADY-EXISTING
-- database (yours), without dropping or losing any data you've already
-- created. Safe to run more than once (IF NOT EXISTS everywhere).

ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(64);
ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMP;

-- Only one account per email, but allow many NULLs (existing accounts
-- created before this migration won't have an email yet).
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email
    ON users(email) WHERE email IS NOT NULL;

-- Fast lookup when a user clicks their reset link.
CREATE INDEX IF NOT EXISTS idx_users_reset_token
    ON users(reset_token) WHERE reset_token IS NOT NULL;
