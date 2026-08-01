"""
Seeds a real demo clinician user into the database, so the login page has
actual credentials to check against. Run once after loading schema_postgres.sql.

Usage: python scripts/seed_demo_user.py
(Run from project root, with HANS_DB_PASSWORD set -- see docs/SETUP.md)
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend", "app", "db"))

from connection import get_connection
from auth import hash_password

DEMO_USERNAME = "nurse_amina"
DEMO_PASSWORD = "TriageDemo2026!"  # change this before any real deployment


def main():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT role_id FROM roles WHERE role_name = 'clinician'")
            row = cur.fetchone()
            if row:
                role_id = row[0]
            else:
                cur.execute("INSERT INTO roles (role_name) VALUES ('clinician') RETURNING role_id")
                role_id = cur.fetchone()[0]

            cur.execute("SELECT user_id FROM users WHERE username = %s", (DEMO_USERNAME,))
            if cur.fetchone():
                print(f"User '{DEMO_USERNAME}' already exists, skipping.")
                return

            password_hash = hash_password(DEMO_PASSWORD)
            cur.execute(
                "INSERT INTO users (username, password_hash, role_id) VALUES (%s, %s, %s)",
                (DEMO_USERNAME, password_hash, role_id),
            )

    print(f"Created demo user:")
    print(f"  username: {DEMO_USERNAME}")
    print(f"  password: {DEMO_PASSWORD}")
    print(f"(Change this password before any real deployment -- this is a demo credential.)")


if __name__ == "__main__":
    main()
