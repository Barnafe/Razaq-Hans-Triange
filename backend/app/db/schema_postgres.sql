-- Module 4.1 - PostgreSQL schema for structured HANS-Triage transactions.
--
-- HONEST STATUS: this is the real production DDL, written carefully against
-- PostgreSQL syntax, but NOT run against a live PostgreSQL server in this
-- build environment (no internet here to install/run Postgres). It IS
-- validated logically via an adapted SQLite version (see
-- backend/app/db/schema_sqlite_test.py) which tests the same structure,
-- constraints, and relationships using an engine we can actually run here.
-- You'll run this real file against your own PostgreSQL instance -- see
-- docs/SETUP.md for the exact steps.

CREATE TABLE roles (
    role_id     SERIAL PRIMARY KEY,
    role_name   VARCHAR(50) UNIQUE NOT NULL  -- e.g. 'clinician', 'admin', 'auditor'
);

CREATE TABLE users (
    user_id       SERIAL PRIMARY KEY,
    username      VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,  -- store bcrypt/argon2 hash, NEVER plaintext
    role_id       INTEGER NOT NULL REFERENCES roles(role_id),
    -- Only meaningful for role='doctor' -- lets the Admin dashboard show
    -- who's available to assign, matching the supervisor's reference
    -- ("Available Doctors" card). Defaults true so existing accounts and
    -- non-doctor roles are unaffected.
    is_available  BOOLEAN NOT NULL DEFAULT TRUE,
    -- Added for email notifications (password reset, approval alerts).
    -- Nullable: accounts created before this feature existed won't have
    -- one until the user sets it, and email is not required to log in.
    email                VARCHAR(255) UNIQUE,
    reset_token          VARCHAR(64),
    reset_token_expires  TIMESTAMP,
    -- Added for email verification (OTP sent at signup): confirms the
    -- email is real and reachable before it's relied on for password
    -- recovery / approval alerts. Nullable/false by default so accounts
    -- created without an email (email is optional) are unaffected.
    email_verified            BOOLEAN NOT NULL DEFAULT FALSE,
    verification_code         VARCHAR(6),
    verification_code_expires TIMESTAMP,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE patients (
    patient_id       SERIAL PRIMARY KEY,
    pseudonym        VARCHAR(50) UNIQUE NOT NULL,  -- deidentified reference, not real name
    age_years        NUMERIC(5,2) NOT NULL,
    sex              VARCHAR(10),
    -- Links a self-registered patient's login to their own patient record,
    -- so their dashboard can find their own history. NULL for patients
    -- recorded by a clinician who never created their own account.
    user_id          INTEGER REFERENCES users(user_id),
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE encounters (
    encounter_id     SERIAL PRIMARY KEY,
    patient_id       INTEGER NOT NULL REFERENCES patients(patient_id),
    recorded_by      INTEGER NOT NULL REFERENCES users(user_id),
    temperature      NUMERIC(4,1),
    heart_rate       NUMERIC(5,1),
    respiratory_rate NUMERIC(5,1),
    systolic         NUMERIC(5,1),
    diastolic        NUMERIC(5,1),
    spo2             NUMERIC(5,1),
    symptoms         JSONB NOT NULL,  -- list of reported symptoms
    created_at       TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE triage_decisions (
    decision_id           SERIAL PRIMARY KEY,
    encounter_id          INTEGER NOT NULL REFERENCES encounters(encounter_id),
    final_tier            VARCHAR(10) NOT NULL,  -- Red/Orange/Yellow/Green/Blue
    bayesian_suggested_tier VARCHAR(10) NOT NULL,
    rule_floor_tier       VARCHAR(10) NOT NULL,
    differential_diagnosis JSONB NOT NULL,
    red_flag_alerts       JSONB,
    rationale             TEXT NOT NULL,
    model_version         VARCHAR(50) NOT NULL,  -- for audit trail
    -- Review/assignment workflow (patient self-submission -> admin review
    -- -> doctor attends). A clinician-recorded encounter (the original
    -- flow, e.g. nurse_amina using the Intake form) is considered already
    -- handled in person, so it defaults straight to 'finalized' and skips
    -- review. Only patient self-submissions start at 'pending_review'.
    --   pending_review -> approved -> attended
    --                  -> rejected
    --   finalized  (clinician-recorded, no review needed)
    status                 VARCHAR(20) NOT NULL DEFAULT 'finalized'
                           CHECK (status IN ('pending_review', 'approved', 'rejected', 'attended', 'finalized')),
    assigned_doctor_id     INTEGER REFERENCES users(user_id),
    reviewed_by            INTEGER REFERENCES users(user_id),  -- the admin who approved/rejected
    reviewed_at            TIMESTAMP,
    rejection_reason       TEXT,
    created_at            TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Module 4.4 - Immutable audit log. Rows are never updated or deleted --
-- application code must only ever INSERT here, enforced by revoking
-- UPDATE/DELETE grants for the application role in production (see
-- docs/SETUP.md Postgres role setup section).
CREATE TABLE audit_log (
    audit_id       SERIAL PRIMARY KEY,
    user_id        INTEGER REFERENCES users(user_id),
    action         VARCHAR(100) NOT NULL,  -- e.g. 'triage_decision_created'
    target_table   VARCHAR(50),
    target_id      INTEGER,
    input_hash     VARCHAR(64),  -- SHA-256 of input payload, for tamper detection
    override_justification TEXT,  -- filled if a clinician overrode the system's suggestion
    timestamp      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_encounters_patient ON encounters(patient_id);
CREATE INDEX idx_triage_encounter ON triage_decisions(encounter_id);
CREATE INDEX idx_triage_status ON triage_decisions(status);
CREATE INDEX idx_triage_assigned_doctor ON triage_decisions(assigned_doctor_id);
CREATE INDEX idx_audit_user ON audit_log(user_id);
