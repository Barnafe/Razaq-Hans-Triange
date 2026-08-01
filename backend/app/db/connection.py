"""
Database connection helper for PostgreSQL. Reads connection details from
environment variables with sensible defaults matching the local setup
from docs/SETUP.md (database name hans_triage, user postgres).

HONEST STATUS: written carefully against psycopg2's documented API, but
NOT runtime-tested in this build environment (no psycopg2/PostgreSQL
available here). You'll be the first to actually run this -- same pattern
as our other database/network-dependent work.
"""
import os
import psycopg2
from contextlib import contextmanager
from dotenv import load_dotenv

# Loads backend/.env once, at import time (this module is imported before
# any env var is read below). This is what lets HANS_DB_PASSWORD (and
# ANTHROPIC_API_KEY for the Chat Agent) survive across terminal sessions
# and across `npm run dev` restarts, instead of needing
# `$env:HANS_DB_PASSWORD = "..."` re-run by hand every time -- the exact
# friction that caused a real "not set" error earlier in this project.
# Copy backend/.env.example to backend/.env and fill in real values once;
# .env itself is gitignored, so secrets never get committed.
#
# encoding="utf-8-sig" is deliberate: Windows PowerShell's
# `Out-File -Encoding utf8` (and some editors' "Save as UTF-8") silently
# prepend a BOM character to the file. Plain "utf-8" decoding leaves that
# BOM glued onto the first variable name (e.g. "\ufeffHANS_DB_PASSWORD"),
# so the real name is never recognized and the var loads as unset --
# this exact failure mode caused a real login/register 500 error. utf-8-sig
# strips a leading BOM if present and is a no-op on files that don't have one.
load_dotenv(
    os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
    encoding="utf-8-sig",
)

DB_HOST = os.environ.get("HANS_DB_HOST", "localhost")
DB_PORT = os.environ.get("HANS_DB_PORT", "5432")
DB_NAME = os.environ.get("HANS_DB_NAME", "hans_triage")
DB_USER = os.environ.get("HANS_DB_USER", "postgres")
DB_PASSWORD = os.environ.get("HANS_DB_PASSWORD")  # required, no default -- see SETUP.md

# Render (and most hosts) provide managed Postgres as a single connection
# string instead of discrete host/port/user/password vars. If DATABASE_URL
# is set, it takes priority over the HANS_DB_* vars above -- this lets the
# exact same code run unchanged locally (HANS_DB_* from backend/.env) and
# in production (DATABASE_URL from Render's environment tab), with zero
# code changes needed at deploy time. See docs/DEPLOY.md.
DATABASE_URL = os.environ.get("DATABASE_URL")


@contextmanager
def get_connection():
    """
    Yields a psycopg2 connection, committing on success and rolling back
    on any exception. Use as: `with get_connection() as conn: ...`
    """
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
    elif DB_PASSWORD is not None:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
        )
    else:
        raise RuntimeError(
            "Neither DATABASE_URL nor HANS_DB_PASSWORD is set. Locally: see "
            "docs/SETUP.md. On Render: see docs/DEPLOY.md."
        )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def db_available() -> bool:
    """
    Checks if the database is reachable, without raising. Used so the API
    can degrade gracefully (still return a triage result even if
    persistence fails) rather than crashing the whole request -- same
    error-isolation philosophy as the agent orchestrator.
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except Exception:
        return False
