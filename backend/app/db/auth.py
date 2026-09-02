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
from datetime import datetime, timedelta, timezone

from connection import get_connection

PBKDF2_ITERATIONS = 260_000
RESET_TOKEN_VALID_MINUTES = 60
VERIFICATION_CODE_VALID_MINUTES = 15


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


class EmailNotVerified(Exception):
    """
    Raised by authenticate() when the credentials are correct but the
    account has an email on file that hasn't been confirmed yet.

    This is what actually makes email verification a real gate rather
    than decoration: an unverified account can be created (see
    register()), but authenticate() refuses to log it in until
    verify_email() has succeeded. Carries the account's email so the
    caller can offer a "verify now" flow without a second lookup.
    """
    def __init__(self, email: str):
        self.email = email
        super().__init__(f"Email '{email}' has not been verified yet")


def authenticate(identifier: str, password: str) -> dict | None:
    """
    Returns {"user_id": ..., "role": ...} on success, None on wrong
    username/password, or raises EmailNotVerified if the password is
    correct but the account's email (if it has one) isn't confirmed yet.
    'identifier' can be either the account's username OR its email --
    the login page has always been labeled "Email or No. Handphone", but
    this only ever matched on username until now, which was a real bug:
    a correct password with an email typed at login always failed.
    Deliberately takes the same shape either way (no early-return timing
    difference) to avoid trivially leaking whether a username exists via
    response timing -- a small but real security consideration.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT u.user_id, u.password_hash, r.role_name, u.email, u.email_verified
                   FROM users u JOIN roles r ON u.role_id = r.role_id
                   WHERE u.username = %s OR u.email = %s""",
                (identifier, identifier),
            )
            row = cur.fetchone()

    if row is None:
        # Still run a hash comparison against a dummy value so failed
        # "user doesn't exist" and failed "wrong password" take
        # comparable time -- reduces username-enumeration risk.
        hash_password(password)
        return None

    user_id, stored_hash, role_name, email, email_verified = row
    if not verify_password(password, stored_hash):
        return None

    # Account exists and the password is right, but if they gave an
    # email at signup it has to be confirmed before the account is
    # usable -- otherwise "verification" was purely cosmetic.
    if email and not email_verified:
        raise EmailNotVerified(email)

    return {"user_id": user_id, "role": role_name}


class UsernameTaken(Exception):
    pass


def register(username: str, password: str, role_name: str = "clinician", email: str | None = None) -> dict:
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
                "INSERT INTO users (username, password_hash, role_id, email) VALUES (%s, %s, %s, %s) RETURNING user_id",
                (username, password_hash, role_id, email),
            )
            user_id = cur.fetchone()[0]

    return {"user_id": user_id, "role": role_name}


def create_password_reset_token(email: str) -> str | None:
    """
    If an account with this email exists, generates a fresh reset token,
    stores it with a 1-hour expiry, and returns it (for the caller to
    email out). Returns None if no account matches this email --
    deliberately silent so the /auth/forgot-password endpoint can always
    respond the same way regardless of whether the email exists, avoiding
    account enumeration via the response.
    """
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_VALID_MINUTES)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE users SET reset_token = %s, reset_token_expires = %s
                   WHERE email = %s RETURNING user_id""",
                (token, expires, email),
            )
            row = cur.fetchone()

    return token if row else None


def reset_password_with_token(token: str, new_password: str) -> bool:
    """
    Verifies the reset token is real and not expired, sets the new
    password, and invalidates the token (single use). Returns False for
    any invalid/expired/already-used token.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT user_id, reset_token_expires FROM users
                   WHERE reset_token = %s""",
                (token,),
            )
            row = cur.fetchone()
            if row is None:
                return False

            user_id, expires = row
            now = datetime.now(timezone.utc)
            # psycopg2 returns a naive datetime for a TIMESTAMP column (no
            # tz info stored) -- compare as naive UTC to match.
            if expires is None or expires.replace(tzinfo=timezone.utc) < now:
                return False

            password_hash = hash_password(new_password)
            cur.execute(
                """UPDATE users SET password_hash = %s, reset_token = NULL,
                   reset_token_expires = NULL WHERE user_id = %s""",
                (password_hash, user_id),
            )

    return True


def generate_verification_code(email: str) -> str | None:
    """
    Creates a fresh 6-digit code for the account with this email, valid
    for 15 minutes, and returns it for the caller to send out. Returns
    None if no account has this email on file. Used both right after
    registration and for a "resend code" request -- calling this again
    simply overwrites any earlier unused code, which is fine since only
    the most recent code should ever work.
    """
    code = f"{secrets.randbelow(1_000_000):06d}"
    expires = datetime.now(timezone.utc) + timedelta(minutes=VERIFICATION_CODE_VALID_MINUTES)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE users SET verification_code = %s, verification_code_expires = %s
                   WHERE email = %s AND email_verified = FALSE RETURNING user_id""",
                (code, expires, email),
            )
            row = cur.fetchone()

    return code if row else None


def verify_email(email: str, code: str) -> bool:
    """
    Checks the code matches and hasn't expired, then marks the account
    verified and clears the code (single use). Returns False for any
    wrong/expired code, or if the email is already verified/unknown.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT user_id, verification_code, verification_code_expires
                   FROM users WHERE email = %s AND email_verified = FALSE""",
                (email,),
            )
            row = cur.fetchone()
            if row is None:
                return False

            user_id, stored_code, expires = row
            now = datetime.now(timezone.utc)
            if (
                stored_code is None
                or expires is None
                or expires.replace(tzinfo=timezone.utc) < now
                or not secrets.compare_digest(stored_code, code)
            ):
                return False

            cur.execute(
                """UPDATE users SET email_verified = TRUE, verification_code = NULL,
                   verification_code_expires = NULL WHERE user_id = %s""",
                (user_id,),
            )

    return True
