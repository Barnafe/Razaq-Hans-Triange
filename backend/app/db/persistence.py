"""
Persistence layer: writes a completed triage decision to PostgreSQL,
closing the gap flagged in Phase 7 -- the API previously computed results
but never saved them, meaning a dashboard would have had no real data.

HONEST STATUS: written against the real schema (schema_postgres.sql) and
psycopg2's documented API, but NOT runtime-tested here (no live
PostgreSQL in this build environment). First real test happens on your
machine.

Uses a fixed system user (created by ensure_system_user, idempotent) for
now, since real per-clinician authentication is being built alongside
this -- see auth.py.
"""
import json
import hashlib
from datetime import datetime, timezone

from connection import get_connection

MODEL_VERSION = "v0.1.0"


def ensure_system_user(conn) -> int:
    """
    Idempotent: creates a 'clinician' role and a 'system' user if they
    don't already exist, returns the user_id. Used as the recorded_by
    user until real per-request authentication is wired through here.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT role_id FROM roles WHERE role_name = 'clinician'")
        row = cur.fetchone()
        if row:
            role_id = row[0]
        else:
            cur.execute("INSERT INTO roles (role_name) VALUES ('clinician') RETURNING role_id")
            role_id = cur.fetchone()[0]

        cur.execute("SELECT user_id FROM users WHERE username = 'system'")
        row = cur.fetchone()
        if row:
            return row[0]

        cur.execute(
            "INSERT INTO users (username, password_hash, role_id) VALUES (%s, %s, %s) RETURNING user_id",
            ("system", "not-a-real-login", role_id),
        )
        return cur.fetchone()[0]


def persist_triage_decision(patient_pseudonym: str, age_years: float, vitals: dict,
                             symptoms: list, triage_output: dict, recorded_by_user_id: int | None = None,
                             status: str = "finalized", patient_user_id: int | None = None) -> dict:
    """
    Writes patient (if new) -> encounter -> triage_decision -> audit_log,
    all within one transaction (get_connection commits/rolls back as a
    unit). Returns the created IDs for reference.

    status: 'finalized' (default, existing clinician-recorded flow, no
    review needed) or 'pending_review' (patient self-submission, must be
    approved by an admin before a doctor sees it).

    patient_user_id: if this is a patient submitting their OWN case, this
    links their patients row to their own login (patients.user_id) so
    their dashboard can find their own submission history. None for the
    existing clinician-recorded flow.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            user_id = recorded_by_user_id or ensure_system_user(conn)

            # Patient: if this is a logged-in patient submitting their own
            # case, reuse THEIR existing patient record (found via
            # user_id) if they have one already -- otherwise every
            # submission would create a new, disconnected patient row
            # since patient_pseudonym is freshly random-generated each
            # time for self-submissions (see main.py's /triage handler).
            # Falls back to the old pseudonym-based lookup/create for the
            # existing clinician-recorded flow (patient_user_id is None).
            patient_id = None
            if patient_user_id is not None:
                cur.execute("SELECT patient_id FROM patients WHERE user_id = %s", (patient_user_id,))
                row = cur.fetchone()
                if row:
                    patient_id = row[0]

            if patient_id is None:
                cur.execute("SELECT patient_id FROM patients WHERE pseudonym = %s", (patient_pseudonym,))
                row = cur.fetchone()
                if row:
                    patient_id = row[0]
                else:
                    cur.execute(
                        "INSERT INTO patients (pseudonym, age_years, user_id) VALUES (%s, %s, %s) RETURNING patient_id",
                        (patient_pseudonym, age_years, patient_user_id),
                    )
                    patient_id = cur.fetchone()[0]

            cur.execute(
                """INSERT INTO encounters
                   (patient_id, recorded_by, temperature, heart_rate, respiratory_rate,
                    systolic, diastolic, spo2, symptoms)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING encounter_id"""
                ,
                (patient_id, user_id, vitals["temperature"], vitals["heart_rate"],
                 vitals["respiratory_rate"], vitals["systolic"], vitals["diastolic"],
                 vitals["spo2"], json.dumps(symptoms)),
            )
            encounter_id = cur.fetchone()[0]

            urgency = triage_output["urgency_classification"]
            cur.execute(
                """INSERT INTO triage_decisions
                   (encounter_id, final_tier, bayesian_suggested_tier, rule_floor_tier,
                    differential_diagnosis, red_flag_alerts, rationale, model_version, status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING decision_id""",
                (encounter_id, urgency["tier"], urgency["tier"], urgency["tier"],
                 json.dumps(triage_output["differential_diagnosis"]),
                 json.dumps(triage_output["red_flag_alerts"]),
                 urgency["rationale"], MODEL_VERSION, status),
            )
            decision_id = cur.fetchone()[0]

            input_payload = {"symptoms": symptoms, "vitals": vitals, "pseudonym": patient_pseudonym}
            input_hash = hashlib.sha256(json.dumps(input_payload, sort_keys=True).encode()).hexdigest()
            cur.execute(
                """INSERT INTO audit_log (user_id, action, target_table, target_id, input_hash)
                   VALUES (%s, %s, %s, %s, %s)""",
                (user_id, "triage_decision_created", "triage_decisions", decision_id, input_hash),
            )

            return {"patient_id": patient_id, "encounter_id": encounter_id, "decision_id": decision_id}


def get_recent_decisions(limit: int = 20) -> list[dict]:
    """
    Fetches the most recent triage decisions, joined with patient/encounter
    info, for the real dashboard (closes the gap flagged in Phase 7 --
    this makes an honest, non-fake dashboard possible).

    Returns full decision detail (not just summary fields) so the
    dashboard can show an expandable row per patient without needing a
    second endpoint or an extra round trip.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT td.decision_id, p.pseudonym, p.age_years, td.final_tier,
                          td.differential_diagnosis, td.created_at, e.symptoms,
                          td.rationale, td.red_flag_alerts, e.temperature,
                          e.heart_rate, e.respiratory_rate, e.systolic,
                          e.diastolic, e.spo2
                   FROM triage_decisions td
                   JOIN encounters e ON td.encounter_id = e.encounter_id
                   JOIN patients p ON e.patient_id = p.patient_id
                   ORDER BY td.created_at DESC
                   LIMIT %s""",
                (limit,),
            )
            rows = cur.fetchall()

    return [
        {
            "decision_id": r[0],
            "pseudonym": r[1],
            "age_years": float(r[2]),
            "tier": r[3],
            # r[4] (differential_diagnosis) is a JSONB column -- psycopg2
            # already deserializes it into a Python list/dict on fetch, so
            # calling json.loads() on it again crashes with "the JSON
            # object must be str, bytes or bytearray, not list". Use it
            # directly instead.
            "top_diagnosis": (r[4][0]["disease"] if r[4] else None),
            "differential_diagnosis": r[4] if r[4] else [],
            "created_at": r[5].isoformat() if isinstance(r[5], datetime) else str(r[5]),
            "symptoms": r[6] if r[6] else [],
            "rationale": r[7],
            "red_flag_alerts": r[8] if r[8] else [],
            "vitals": {
                "temperature": float(r[9]) if r[9] is not None else None,
                "heart_rate": float(r[10]) if r[10] is not None else None,
                "respiratory_rate": float(r[11]) if r[11] is not None else None,
                "systolic": float(r[12]) if r[12] is not None else None,
                "diastolic": float(r[13]) if r[13] is not None else None,
                "spo2": float(r[14]) if r[14] is not None else None,
            },
        }
        for r in rows
    ]


def get_all_users() -> list[dict]:
    """
    Real, honest admin-relevant data: the actual list of registered users
    and their roles. No fake hospital-ops metrics -- this is genuine data
    we actually have.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT u.username, r.role_name, u.created_at
                   FROM users u JOIN roles r ON u.role_id = r.role_id
                   ORDER BY u.created_at DESC"""
            )
            rows = cur.fetchall()

    return [
        {
            "username": r[0],
            "role": r[1],
            "created_at": r[2].isoformat() if isinstance(r[2], datetime) else str(r[2]),
        }
        for r in rows
    ]


def _decision_row_to_dict(r: tuple) -> dict:
    """
    Shared row->dict shape for the review-workflow queries below (same
    column order as their SELECT statements) -- keeps get_pending_decisions,
    get_assigned_decisions, and get_patient_history consistent with each
    other and with get_recent_decisions' shape.
    """
    return {
        "decision_id": r[0],
        "pseudonym": r[1],
        "age_years": float(r[2]),
        "tier": r[3],
        "top_diagnosis": (r[4][0]["disease"] if r[4] else None),
        "differential_diagnosis": r[4] if r[4] else [],
        "created_at": r[5].isoformat() if isinstance(r[5], datetime) else str(r[5]),
        "symptoms": r[6] if r[6] else [],
        "rationale": r[7],
        "red_flag_alerts": r[8] if r[8] else [],
        "status": r[9],
    }


_DECISION_SELECT_COLUMNS = """td.decision_id, p.pseudonym, p.age_years, td.final_tier,
       td.differential_diagnosis, td.created_at, e.symptoms, td.rationale,
       td.red_flag_alerts, td.status"""


def get_pending_decisions() -> list[dict]:
    """Cases awaiting admin review (patient self-submissions only)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT {_DECISION_SELECT_COLUMNS}
                    FROM triage_decisions td
                    JOIN encounters e ON td.encounter_id = e.encounter_id
                    JOIN patients p ON e.patient_id = p.patient_id
                    WHERE td.status = 'pending_review'
                    ORDER BY td.created_at ASC"""
            )
            rows = cur.fetchall()
    return [_decision_row_to_dict(r) for r in rows]


def get_available_doctors() -> list[dict]:
    """Doctors an admin can assign a case to right now."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT u.user_id, u.username
                   FROM users u JOIN roles r ON u.role_id = r.role_id
                   WHERE r.role_name = 'doctor' AND u.is_available = TRUE
                   ORDER BY u.username"""
            )
            rows = cur.fetchall()
    return [{"user_id": r[0], "username": r[1]} for r in rows]


class DecisionNotPending(Exception):
    """Raised when trying to approve/reject a decision that isn't awaiting review."""


def approve_decision(decision_id: int, doctor_id: int, admin_user_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE triage_decisions
                   SET status = 'approved', assigned_doctor_id = %s,
                       reviewed_by = %s, reviewed_at = NOW()
                   WHERE decision_id = %s AND status = 'pending_review'""",
                (doctor_id, admin_user_id, decision_id),
            )
            if cur.rowcount == 0:
                raise DecisionNotPending(
                    f"Decision {decision_id} is not awaiting review (already actioned, or doesn't exist)."
                )


def reject_decision(decision_id: int, admin_user_id: int, reason: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE triage_decisions
                   SET status = 'rejected', reviewed_by = %s,
                       reviewed_at = NOW(), rejection_reason = %s
                   WHERE decision_id = %s AND status = 'pending_review'""",
                (admin_user_id, reason, decision_id),
            )
            if cur.rowcount == 0:
                raise DecisionNotPending(
                    f"Decision {decision_id} is not awaiting review (already actioned, or doesn't exist)."
                )


def get_assigned_decisions(doctor_user_id: int) -> list[dict]:
    """Cases assigned to this doctor (approved and/or already attended)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT {_DECISION_SELECT_COLUMNS}
                    FROM triage_decisions td
                    JOIN encounters e ON td.encounter_id = e.encounter_id
                    JOIN patients p ON e.patient_id = p.patient_id
                    WHERE td.assigned_doctor_id = %s
                    ORDER BY td.reviewed_at DESC""",
                (doctor_user_id,),
            )
            rows = cur.fetchall()
    return [_decision_row_to_dict(r) for r in rows]


class NotAssignedToDoctor(Exception):
    """Raised when a doctor tries to act on a case that isn't assigned to them."""


def mark_attended(decision_id: int, doctor_user_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE triage_decisions SET status = 'attended'
                   WHERE decision_id = %s AND assigned_doctor_id = %s AND status = 'approved'""",
                (decision_id, doctor_user_id),
            )
            if cur.rowcount == 0:
                raise NotAssignedToDoctor(
                    f"Decision {decision_id} is not an approved case assigned to this doctor."
                )


def get_admin_dashboard_stats() -> dict:
    """
    Everything the redesigned Admin dashboard needs in one call: real
    counts (no fake hospital-ops numbers), a diagnosis breakdown, a
    7-day assessment trend, and a recent-activity feed built from real
    status transitions (submitted / approved+assigned / rejected /
    attended / clinician-recorded), not fabricated names.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM patients")
            total_patients = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM triage_decisions WHERE status = 'pending_review'")
            pending_count = cur.fetchone()[0]

            cur.execute(
                """SELECT COUNT(*) FROM users u JOIN roles r ON u.role_id = r.role_id
                   WHERE r.role_name = 'doctor' AND u.is_available = TRUE"""
            )
            available_doctors_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM triage_decisions")
            total_assessments = cur.fetchone()[0]

            cur.execute("SELECT final_tier, COUNT(*) FROM triage_decisions GROUP BY final_tier")
            tier_counts = {r[0]: r[1] for r in cur.fetchall()}

            # differential_diagnosis is JSONB -- psycopg2 already returns it
            # as a Python list, no json.loads() (see the earlier JSONB bug).
            cur.execute("SELECT differential_diagnosis FROM triage_decisions")
            diag_rows = cur.fetchall()

            cur.execute(
                """SELECT DATE(created_at), COUNT(*) FROM triage_decisions
                   WHERE created_at >= NOW() - INTERVAL '7 days'
                   GROUP BY DATE(created_at) ORDER BY DATE(created_at)"""
            )
            by_day_rows = cur.fetchall()

            cur.execute(
                """SELECT p.pseudonym, td.status, td.created_at, td.reviewed_at, du.username
                   FROM triage_decisions td
                   JOIN encounters e ON td.encounter_id = e.encounter_id
                   JOIN patients p ON e.patient_id = p.patient_id
                   LEFT JOIN users du ON td.assigned_doctor_id = du.user_id
                   ORDER BY COALESCE(td.reviewed_at, td.created_at) DESC
                   LIMIT 8"""
            )
            activity_rows = cur.fetchall()

    diagnosis_counts: dict[str, int] = {}
    for (dd,) in diag_rows:
        if dd:
            top = dd[0]["disease"]
            diagnosis_counts[top] = diagnosis_counts.get(top, 0) + 1
    diagnosis_breakdown = sorted(
        [{"disease": k, "count": v} for k, v in diagnosis_counts.items()],
        key=lambda x: -x["count"],
    )[:6]

    assessments_by_day = [{"date": str(d), "count": c} for d, c in by_day_rows]

    status_text = {
        "pending_review": lambda p, doc: f"{p} submitted a new assessment, awaiting review",
        "approved": lambda p, doc: f"{p}'s case approved" + (f", assigned to Dr. {doc}" if doc else ""),
        "rejected": lambda p, doc: f"{p}'s case reviewed and rejected",
        "attended": lambda p, doc: f"{p}'s case attended" + (f" by Dr. {doc}" if doc else ""),
        "finalized": lambda p, doc: f"Assessment recorded for {p}",
    }
    recent_activity = []
    for pseudonym, status, created_at, reviewed_at, doctor_username in activity_rows:
        ts = reviewed_at if (reviewed_at and status != "pending_review") else created_at
        text_fn = status_text.get(status, status_text["finalized"])
        recent_activity.append({
            "text": text_fn(pseudonym, doctor_username),
            "timestamp": ts.isoformat() if isinstance(ts, datetime) else str(ts),
        })

    return {
        "total_patients": total_patients,
        "pending_count": pending_count,
        "available_doctors_count": available_doctors_count,
        "total_assessments": total_assessments,
        "tier_counts": tier_counts,
        "diagnosis_breakdown": diagnosis_breakdown,
        "assessments_by_day": assessments_by_day,
        "recent_activity": recent_activity,
    }


def get_patient_history(patient_user_id: int) -> list[dict]:
    """A patient's own past submissions and their current status."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT {_DECISION_SELECT_COLUMNS}
                    FROM triage_decisions td
                    JOIN encounters e ON td.encounter_id = e.encounter_id
                    JOIN patients p ON e.patient_id = p.patient_id
                    WHERE p.user_id = %s
                    ORDER BY td.created_at DESC""",
                (patient_user_id,),
            )
            rows = cur.fetchall()
    return [_decision_row_to_dict(r) for r in rows]


def get_decision_notification_info(decision_id: int) -> dict | None:
    """
    What's needed to notify a patient their case was approved: their own
    email (via patient -> user), the assigned doctor's username, and the
    final tier. Returns None if the patient never registered their own
    account (email/reset are self-service, so a clinician-recorded
    patient with no login simply has nothing to notify) or has no email
    on file -- callers should skip sending in that case, not error.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT pu.email, doc.username, td.final_tier
                   FROM triage_decisions td
                   JOIN encounters e ON td.encounter_id = e.encounter_id
                   JOIN patients p ON e.patient_id = p.patient_id
                   LEFT JOIN users pu ON p.user_id = pu.user_id
                   LEFT JOIN users doc ON td.assigned_doctor_id = doc.user_id
                   WHERE td.decision_id = %s""",
                (decision_id,),
            )
            row = cur.fetchone()

    if row is None or row[0] is None:
        return None
    return {"patient_email": row[0], "doctor_username": row[1], "tier": row[2]}
