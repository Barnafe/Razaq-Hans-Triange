"""
Real authentication: password hashing (PBKDF2-HMAC-SHA256, stdlib only,
no new dependency) and credential verification against the real
PostgreSQL users table -- closes the gap flagged since Phase 7, where
the login UI existed but nothing checked credentials.

HONEST STATUS: written against psycopg2's documented API, NOT
runtime-tested here (no live PostgreSQL in this build environment).

HONEST SCOPE NOTE: this is real credential verification (a wrong
password genuinely fails), but there is no session/token issuance --
after a successful login, the frontend just proceeds, the same way it
did before. A production system would issue a JWT or session cookie and
check it on every subsequent request. That's flagged here as the next
real step, not silently skipped.
"""
import hashlib
import os
import secrets

from connection import get_connection

PBKDF2_ITERATIONS = 260_000


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Returns 'salt_hex$hash_hex', both hex-encoded for easy storage as text."""
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, digest_hex = stored_hash.split("$")
    except ValueError:
        return False  # malformed hash, never match
    salt = bytes.fromhex(salt_hex)
    expected = hash_password(password, salt)
    return secrets.compare_digest(expected, stored_hash)


def authenticate(username: str, password: str) -> dict | None:
    """
    Returns {"user_id": ..., "role": ...} on success, None on failure.
    Deliberately takes the same shape either way (no early-return timing
    difference) to avoid trivially leaking whether a username exists via
    response timing -- a small but real security consideration.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT u.user_id, u.password_hash, r.role_name
                   FROM users u JOIN roles r ON u.role_id = r.role_id
                   WHERE u.username = %s""",
                (username,),
            )
            row = cur.fetchone()

    if row is None:
        # Still run a hash comparison against a dummy value so failed
        # "user doesn't exist" and failed "wrong password" take
        # comparable time -- reduces username-enumeration risk.
        hash_password(password)
        return None

    user_id, stored_hash, role_name = row
    if not verify_password(password, stored_hash):
        return None

    return {"user_id": user_id, "role": role_name}


class UsernameTaken(Exception):
    pass


def register(username: str, password: str, role_name: str = "clinician") -> dict:
    """
    Creates a new user with a properly hashed password. Raises
    UsernameTaken if the username already exists (checked explicitly so
    the caller gets a clear, specific error rather than a generic
    database constraint violation).
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                raise UsernameTaken(f"Username '{username}' is already taken")

            cur.execute("SELECT role_id FROM roles WHERE role_name = %s", (role_name,))
            row = cur.fetchone()
            if row:
                role_id = row[0]
            else:
                cur.execute("INSERT INTO roles (role_name) VALUES (%s) RETURNING role_id", (role_name,))
                role_id = cur.fetchone()[0]

            password_hash = hash_password(password)
            cur.execute(
                "INSERT INTO users (username, password_hash, role_id) VALUES (%s, %s, %s) RETURNING user_id",
                (username, password_hash, role_id),
            )
            user_id = cur.fetchone()[0]

    return {"user_id": user_id, "role": role_name}
