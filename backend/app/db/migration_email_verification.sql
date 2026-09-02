-- Migration: adds email verification (OTP code) to an ALREADY-EXISTING
-- database (yours), without dropping or losing any data. Safe to run
-- more than once (IF NOT EXISTS everywhere).

ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_code VARCHAR(6);
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_code_expires TIMESTAMP;
