"""
Module 4.1 (validation) - SQLite-adapted version of schema_postgres.sql,
used to genuinely test the schema's structure, constraints, and query
logic in this build environment (no live PostgreSQL available here).

Differences from the Postgres DDL (syntax only, not logic):
  SERIAL -> INTEGER PRIMARY KEY AUTOINCREMENT
  JSONB  -> TEXT (storing JSON as a string; SQLite has no native JSON type)
  NOW()  -> CURRENT_TIMESTAMP

This is a validation tool, not the production schema -- schema_postgres.sql
is what actually gets deployed to your real PostgreSQL instance.
"""
import sqlite3
import json
import hashlib


SCHEMA_SQLITE = """
CREATE TABLE roles (
    role_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name   TEXT UNIQUE NOT NULL
);

CREATE TABLE users (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role_id       INTEGER NOT NULL REFERENCES roles(role_id),
    is_available  INTEGER NOT NULL DEFAULT 1,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE patients (
    patient_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    pseudonym        TEXT UNIQUE NOT NULL,
    age_years        REAL NOT NULL,
    sex              TEXT,
    user_id          INTEGER REFERENCES users(user_id),
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE encounters (
    encounter_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id       INTEGER NOT NULL REFERENCES patients(patient_id),
    recorded_by      INTEGER NOT NULL REFERENCES users(user_id),
    temperature      REAL,
    heart_rate       REAL,
    respiratory_rate REAL,
    systolic         REAL,
    diastolic        REAL,
    spo2             REAL,
    symptoms         TEXT NOT NULL,
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE triage_decisions (
    decision_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    encounter_id          INTEGER NOT NULL REFERENCES encounters(encounter_id),
    final_tier            TEXT NOT NULL,
    bayesian_suggested_tier TEXT NOT NULL,
    rule_floor_tier       TEXT NOT NULL,
    differential_diagnosis TEXT NOT NULL,
    red_flag_alerts       TEXT,
    rationale             TEXT NOT NULL,
    model_version         TEXT NOT NULL,
    status                 TEXT NOT NULL DEFAULT 'finalized'
                           CHECK (status IN ('pending_review', 'approved', 'rejected', 'attended', 'finalized')),
    assigned_doctor_id     INTEGER REFERENCES users(user_id),
    reviewed_by            INTEGER REFERENCES users(user_id),
    reviewed_at            TIMESTAMP,
    rejection_reason       TEXT,
    created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
    audit_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER REFERENCES users(user_id),
    action         TEXT NOT NULL,
    target_table   TEXT,
    target_id      INTEGER,
    input_hash     TEXT,
    override_justification TEXT,
    timestamp      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def build_test_db():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA_SQLITE)
    return conn


def demo_full_flow():
    """
    Simulates one full encounter -> triage decision -> audit log write,
    proving the schema's foreign-key relationships and constraints work
    end-to-end (matches Module 4.4's audit trail requirement).
    """
    conn = build_test_db()
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    cur.execute("INSERT INTO roles (role_name) VALUES ('clinician')")
    role_id = cur.lastrowid

    cur.execute(
        "INSERT INTO users (username, password_hash, role_id) VALUES (?, ?, ?)",
        ("nurse_amina", "fake_hash_for_testing_only", role_id),
    )
    user_id = cur.lastrowid

    cur.execute(
        "INSERT INTO patients (pseudonym, age_years, sex) VALUES (?, ?, ?)",
        ("PT-0001", 8, "F"),
    )
    patient_id = cur.lastrowid

    symptoms = json.dumps(["Fever", "Headache", "Stiff neck", "Altered consciousness"])
    cur.execute(
        """INSERT INTO encounters
           (patient_id, recorded_by, temperature, heart_rate, respiratory_rate,
            systolic, diastolic, spo2, symptoms)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (patient_id, user_id, 39.5, 130, 28, 95, 60, 92, symptoms),
    )
    encounter_id = cur.lastrowid

    differential = json.dumps([{"disease": "Bacterial Meningitis", "probability": 0.837}])
    input_payload = f"{patient_id}-{encounter_id}-{symptoms}"
    input_hash = hashlib.sha256(input_payload.encode()).hexdigest()

    cur.execute(
        """INSERT INTO triage_decisions
           (encounter_id, final_tier, bayesian_suggested_tier, rule_floor_tier,
            differential_diagnosis, red_flag_alerts, rationale, model_version)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (encounter_id, "Red", "Orange", "Red", differential,
         json.dumps(["NEUROLOGICAL DANGER SIGN", "POSSIBLE MENINGITIS"]),
         "Bayesian model suggested Orange; rule floor was Red (altered "
         "consciousness + stiff neck); final = Red.", "v0.1.0"),
    )
    decision_id = cur.lastrowid

    cur.execute(
        """INSERT INTO audit_log (user_id, action, target_table, target_id, input_hash)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, "triage_decision_created", "triage_decisions", decision_id, input_hash),
    )

    conn.commit()

    # Verify: query back joined data, confirm constraints held
    cur.execute("""
        SELECT p.pseudonym, u.username, td.final_tier, td.rationale, a.input_hash
        FROM triage_decisions td
        JOIN encounters e ON td.encounter_id = e.encounter_id
        JOIN patients p ON e.patient_id = p.patient_id
        JOIN users u ON e.recorded_by = u.user_id
        JOIN audit_log a ON a.target_id = td.decision_id
        WHERE td.decision_id = ?
    """, (decision_id,))
    row = cur.fetchone()

    print("Full flow test -- joined query result:")
    print(f"  Patient: {row[0]}, recorded by: {row[1]}, tier: {row[2]}")
    print(f"  Rationale: {row[3]}")
    print(f"  Audit hash: {row[4]}")

    # Test constraint enforcement: try inserting an encounter for a
    # nonexistent patient, should fail (foreign key constraint)
    try:
        cur.execute(
            """INSERT INTO encounters
               (patient_id, recorded_by, symptoms) VALUES (9999, ?, '[]')""",
            (user_id,),
        )
        conn.commit()
        print("\nFAIL: foreign key constraint did not block invalid patient_id")
    except sqlite3.IntegrityError as e:
        print(f"\nPASS: foreign key constraint correctly blocked invalid insert ({e})")

    conn.close()


def demo_review_workflow():
    """
    Simulates the full patient-submit -> admin-review -> doctor-attend
    workflow end-to-end, proving the new status/assignment columns and
    their relationships work correctly. This is the one part of the new
    review workflow that can genuinely be *run* in this build environment
    (no live PostgreSQL here) -- everything else was verified by careful
    reading + py_compile only, same honesty pattern as the rest of this
    project.
    """
    conn = build_test_db()
    conn.execute("PRAGMA foreign_keys = ON")
    cur = conn.cursor()

    # Set up roles
    cur.execute("INSERT INTO roles (role_name) VALUES ('patient')")
    patient_role_id = cur.lastrowid
    cur.execute("INSERT INTO roles (role_name) VALUES ('doctor')")
    doctor_role_id = cur.lastrowid
    cur.execute("INSERT INTO roles (role_name) VALUES ('admin')")
    admin_role_id = cur.lastrowid

    # A patient registers their own account
    cur.execute(
        "INSERT INTO users (username, password_hash, role_id) VALUES (?, ?, ?)",
        ("patient_musa", "fake_hash_for_testing_only", patient_role_id),
    )
    patient_user_id = cur.lastrowid

    # Two doctors, one available and one not -- proves the availability
    # filter works for the Admin dashboard's doctor-assignment picker
    cur.execute(
        "INSERT INTO users (username, password_hash, role_id, is_available) VALUES (?, ?, ?, ?)",
        ("dr_bello", "fake_hash_for_testing_only", doctor_role_id, 1),
    )
    available_doctor_id = cur.lastrowid
    cur.execute(
        "INSERT INTO users (username, password_hash, role_id, is_available) VALUES (?, ?, ?, ?)",
        ("dr_okafor", "fake_hash_for_testing_only", doctor_role_id, 0),
    )
    cur.lastrowid  # unavailable doctor, intentionally not assigned

    # An admin account
    cur.execute(
        "INSERT INTO users (username, password_hash, role_id) VALUES (?, ?, ?)",
        ("admin_hauwa", "fake_hash_for_testing_only", admin_role_id),
    )
    admin_user_id = cur.lastrowid

    # Patient's own patient record, linked via user_id
    cur.execute(
        "INSERT INTO patients (pseudonym, age_years, sex, user_id) VALUES (?, ?, ?, ?)",
        ("PT-SELF-0001", 29, "M", patient_user_id),
    )
    self_patient_id = cur.lastrowid

    # Patient submits their own encounter -- recorded_by is their own
    # user_id (not a clinician's), matching "patient submits it themself"
    symptoms = json.dumps(["Fever", "Cough", "Fatigue"])
    cur.execute(
        """INSERT INTO encounters
           (patient_id, recorded_by, temperature, heart_rate, respiratory_rate,
            systolic, diastolic, spo2, symptoms)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (self_patient_id, patient_user_id, 38.2, 95, 20, 118, 76, 97, symptoms),
    )
    encounter_id = cur.lastrowid

    # Triage decision starts as pending_review (patient self-submission)
    differential = json.dumps([{"disease": "Uncomplicated Malaria", "probability": 0.71}])
    cur.execute(
        """INSERT INTO triage_decisions
           (encounter_id, final_tier, bayesian_suggested_tier, rule_floor_tier,
            differential_diagnosis, rationale, model_version, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (encounter_id, "Yellow", "Yellow", "Green", differential,
         "Self-reported fever + cough, no danger signs.", "v0.1.0", "pending_review"),
    )
    decision_id = cur.lastrowid
    conn.commit()

    # Verify: it shows up in the admin's pending-review queue
    cur.execute("SELECT decision_id, status FROM triage_decisions WHERE status = 'pending_review'")
    pending = cur.fetchall()
    assert len(pending) == 1 and pending[0][0] == decision_id, "pending_review queue query failed"
    print("PASS: pending_review queue correctly shows the new submission")

    # Verify: the available-doctors query only returns dr_bello
    cur.execute(
        """SELECT u.username FROM users u JOIN roles r ON u.role_id = r.role_id
           WHERE r.role_name = 'doctor' AND u.is_available = 1"""
    )
    available = [r[0] for r in cur.fetchall()]
    assert available == ["dr_bello"], f"available-doctors filter failed, got {available}"
    print("PASS: available-doctors query correctly excludes dr_okafor (is_available=0)")

    # Admin approves and assigns dr_bello
    cur.execute(
        """UPDATE triage_decisions
           SET status = 'approved', assigned_doctor_id = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
           WHERE decision_id = ?""",
        (available_doctor_id, admin_user_id, decision_id),
    )
    conn.commit()

    # Verify: it now shows up in dr_bello's assigned-patients list
    cur.execute(
        """SELECT p.pseudonym, td.final_tier, td.status
           FROM triage_decisions td
           JOIN encounters e ON td.encounter_id = e.encounter_id
           JOIN patients p ON e.patient_id = p.patient_id
           WHERE td.assigned_doctor_id = ?""",
        (available_doctor_id,),
    )
    assigned = cur.fetchall()
    assert len(assigned) == 1 and assigned[0][0] == "PT-SELF-0001", "doctor's assigned-list query failed"
    print(f"PASS: doctor's assigned-patients list shows {assigned[0][0]} (tier {assigned[0][1]}, status {assigned[0][2]})")

    # Doctor marks the case attended
    cur.execute(
        "UPDATE triage_decisions SET status = 'attended' WHERE decision_id = ? AND assigned_doctor_id = ?",
        (decision_id, available_doctor_id),
    )
    conn.commit()
    cur.execute("SELECT status FROM triage_decisions WHERE decision_id = ?", (decision_id,))
    final_status = cur.fetchone()[0]
    assert final_status == "attended", f"expected attended, got {final_status}"
    print("PASS: full workflow reached 'attended' status correctly")

    # Verify a bad status value is rejected by the CHECK constraint
    try:
        cur.execute(
            "UPDATE triage_decisions SET status = 'not_a_real_status' WHERE decision_id = ?",
            (decision_id,),
        )
        conn.commit()
        print("FAIL: CHECK constraint did not reject an invalid status value")
    except sqlite3.IntegrityError as e:
        print(f"PASS: CHECK constraint correctly rejected an invalid status value ({e})")

    # Verify clinician-recorded encounters still default to 'finalized'
    # (unchanged behavior -- proves the new column doesn't break the
    # existing clinician-intake flow from earlier phases)
    cur.execute("INSERT INTO roles (role_name) VALUES ('clinician')")
    clinician_role_id = cur.lastrowid
    cur.execute(
        "INSERT INTO users (username, password_hash, role_id) VALUES (?, ?, ?)",
        ("nurse_amina", "fake_hash_for_testing_only", clinician_role_id),
    )
    clinician_id = cur.lastrowid
    cur.execute(
        "INSERT INTO patients (pseudonym, age_years, sex) VALUES (?, ?, ?)",
        ("PT-CLINIC-0001", 5, "F"),
    )
    clinic_patient_id = cur.lastrowid
    cur.execute(
        """INSERT INTO encounters (patient_id, recorded_by, symptoms) VALUES (?, ?, ?)""",
        (clinic_patient_id, clinician_id, json.dumps(["Fever"])),
    )
    clinic_encounter_id = cur.lastrowid
    cur.execute(
        """INSERT INTO triage_decisions
           (encounter_id, final_tier, bayesian_suggested_tier, rule_floor_tier,
            differential_diagnosis, rationale, model_version)
           VALUES (?, 'Green', 'Green', 'Green', ?, 'Routine.', 'v0.1.0')""",
        (clinic_encounter_id, json.dumps([{"disease": "Common Cold", "probability": 0.6}])),
    )
    clinic_decision_id = cur.lastrowid
    conn.commit()
    cur.execute("SELECT status FROM triage_decisions WHERE decision_id = ?", (clinic_decision_id,))
    assert cur.fetchone()[0] == "finalized", "clinician-recorded encounter should default to 'finalized'"
    print("PASS: clinician-recorded encounters still default to 'finalized' (existing flow unaffected)")

    conn.close()


if __name__ == "__main__":
    demo_full_flow()
    print()
    demo_review_workflow()
