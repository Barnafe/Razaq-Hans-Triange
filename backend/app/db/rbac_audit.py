"""
Module 4.3/4.4 - Role-Based Access Control + Immutable Audit Logging

RBAC: simple role -> permission mapping, checked before any sensitive
action. Deidentification is handled at the schema level (patients.pseudonym,
not real names -- see schema_postgres.sql) rather than here.

AUDIT LOG IMMUTABILITY: enforced at TWO levels, defense-in-depth:
  1. Application level (this file): AuditLogger only exposes an `append()`
     method -- there is deliberately no update/delete method to call.
  2. Database level (production): the application's Postgres role should
     have UPDATE/DELETE privileges REVOKED on the audit_log table entirely,
     so even a bug or compromised credential can't rewrite history. Exact
     SQL for this is in docs/SETUP.md's Postgres setup section.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json


# --- RBAC ---

PERMISSIONS = {
    "clinician": {"view_patient", "create_encounter", "view_triage_decision", "override_triage"},
    "admin": {"view_patient", "create_encounter", "view_triage_decision", "manage_users"},
    "auditor": {"view_audit_log"},
}


class PermissionDenied(Exception):
    pass


def check_permission(role: str, action: str) -> None:
    """Raises PermissionDenied if the role isn't allowed to perform action."""
    allowed = PERMISSIONS.get(role, set())
    if action not in allowed:
        raise PermissionDenied(f"Role '{role}' is not permitted to perform '{action}'")


# --- Immutable audit log ---

@dataclass
class AuditEntry:
    user_id: int
    action: str
    target_table: str
    target_id: int
    input_hash: str
    timestamp: str
    override_justification: str | None = None


class AuditLogger:
    """
    Append-only by design: this class deliberately has no update() or
    delete() method. In production this is backed by the audit_log table
    (schema_postgres.sql), with DB-level grants also preventing modification
    -- see module docstring.
    """
    def __init__(self):
        self._entries: list[AuditEntry] = []

    def append(self, user_id: int, action: str, target_table: str, target_id: int,
               payload: dict, override_justification: str | None = None) -> AuditEntry:
        input_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True).encode()
        ).hexdigest()

        entry = AuditEntry(
            user_id=user_id,
            action=action,
            target_table=target_table,
            target_id=target_id,
            input_hash=input_hash,
            timestamp=datetime.now(timezone.utc).isoformat(),
            override_justification=override_justification,
        )
        self._entries.append(entry)
        return entry

    def all_entries(self) -> list[AuditEntry]:
        """Read-only view -- no way to mutate self._entries from outside."""
        return list(self._entries)


if __name__ == "__main__":
    print("--- RBAC test ---")
    try:
        check_permission("auditor", "override_triage")
        print("FAIL: auditor should not be able to override triage")
    except PermissionDenied as e:
        print(f"PASS: {e}")

    check_permission("clinician", "override_triage")
    print("PASS: clinician correctly allowed to override_triage")

    print("\n--- Audit log test ---")
    logger = AuditLogger()
    entry = logger.append(
        user_id=1, action="triage_decision_created", target_table="triage_decisions",
        target_id=42, payload={"final_tier": "Red", "patient_id": 7},
    )
    print(f"Logged entry: {entry}")

    override_entry = logger.append(
        user_id=1, action="triage_decision_overridden", target_table="triage_decisions",
        target_id=42, payload={"new_tier": "Orange"},
        override_justification="Clinician assessed patient as stable on re-exam; "
                                "documented in physical chart #4471.",
    )
    print(f"Logged override with justification: {override_entry.override_justification}")

    print(f"\nTotal audit entries: {len(logger.all_entries())}")
    print("Confirming no update/delete method exists:",
          not hasattr(logger, "update"), not hasattr(logger, "delete"))
