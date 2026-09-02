"""
Module 3.2 (web layer) - FastAPI application exposing the agent
orchestrator over HTTP.

NOTE: FastAPI/pydantic/uvicorn are not installed in the build environment
(no internet access there), so this file has NOT been runtime-tested by
running a live server -- only reviewed carefully against FastAPI's
documented API. You will be the first to actually run this; if something
doesn't work, paste the error back and we'll fix it together.

Run locally with (after `pip install -r requirements.txt`):
    uvicorn main:app --reload --port 8000
Then visit http://localhost:8000/docs for the interactive API explorer.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "db"))

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
import io
import uuid
from PIL import Image

from orchestrator import run_pipeline
from rule_engine import PatientInput
from vision_agent import inflammation_score, vision_flag_for_triage
from auth import (
    authenticate, register, UsernameTaken, EmailNotVerified, create_password_reset_token,
    reset_password_with_token, generate_verification_code, verify_email,
)
from persistence import (
    persist_triage_decision, get_recent_decisions, get_all_users,
    get_pending_decisions, get_available_doctors, approve_decision,
    reject_decision, get_assigned_decisions, mark_attended, get_patient_history,
    get_admin_dashboard_stats, get_decision_notification_info, DecisionNotPending, NotAssignedToDoctor,
)
from connection import db_available
from notifications import send_password_reset_email, send_approval_notification, send_verification_email

app = FastAPI(
    title="HANS-Triage API",
    description="Disease Symptom-Based Triage and Clinical Decision Support System",
    version="0.1.0",
)


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    # 'clinician', 'admin', 'patient', or 'doctor' -- see /auth/register
    # for the honest limitation on self-selecting 'admin'/'doctor'.
    role: str = "clinician"
    # Optional: not required to register/log in, but required if the
    # user ever wants to use "Forgot Password?" or receive approval
    # notifications -- both are email-address-based, not username-based.
    email: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    email: str
    code: str


class ResendVerificationRequest(BaseModel):
    email: str


class ApproveRequest(BaseModel):
    doctor_id: int = Field(..., description="user_id of the doctor to assign this case to")
    admin_user_id: int = Field(..., description="user_id of the admin approving this case")


class RejectRequest(BaseModel):
    admin_user_id: int = Field(..., description="user_id of the admin rejecting this case")
    reason: str = Field(..., description="Why this submission is being rejected")


class AttendRequest(BaseModel):
    doctor_id: int = Field(..., description="user_id of the doctor marking this case attended")


class TriageRequest(BaseModel):
    symptoms: list[str] = Field(..., description="List of present symptoms from the checkbox intake form")
    temperature: float = Field(..., description="Body temperature in Celsius")
    heart_rate: float = Field(..., description="Heart rate in bpm")
    respiratory_rate: float = Field(..., description="Respiratory rate per minute")
    systolic: float = Field(..., description="Systolic blood pressure, mmHg")
    diastolic: float = Field(..., description="Diastolic blood pressure, mmHg")
    spo2: float = Field(..., description="Oxygen saturation, percent")
    age_years: float = Field(..., description="Patient age in years (use fractional for infants, e.g. 0.5 for 6 months)")
    chat_message: str | None = Field(None, description="Optional free-text message for the Chat Agent")
    has_vision_red_flag: bool = Field(
        False,
        description="Set this to the 'flag' value returned by /vision-check, "
                     "if an image was uploaded and analyzed first. Defaults to "
                     "False (no image / no red flag).",
    )
    patient_pseudonym: str | None = Field(
        None, description="Optional patient reference ID. Auto-generated if not provided."
    )
    self_submitted: bool = Field(
        False,
        description="True if a logged-in patient is submitting their OWN case "
                     "(goes to admin review before a doctor sees it), instead of "
                     "a clinician recording it directly (finalized immediately).",
    )
    submitted_by_user_id: int | None = Field(
        None, description="Required if self_submitted is true -- the patient's own user_id."
    )


@app.get("/health")
def health_check():
    return {"status": "HANS-Triage API is running", "database_available": db_available()}


@app.post("/auth/login")
def login(request: LoginRequest):
    """
    Real credential verification against the PostgreSQL users table.
    HONEST SCOPE NOTE: no session/token is issued on success -- see
    backend/app/db/auth.py's module docstring for what a production
    version would add here.
    """
    try:
        result = authenticate(request.username, request.password)
    except EmailNotVerified as e:
        # Correct password, but the account's email is still unconfirmed
        # -- this is the actual verification gate (see auth.py). detail
        # is a structured dict, not a plain string, so the frontend can
        # pull out the email and drop the user straight into the
        # "enter your code" flow instead of just showing an error.
        raise HTTPException(
            status_code=403,
            detail={"error": "email_not_verified", "email": e.email},
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"status": "ok", "user_id": result["user_id"], "role": result["role"]}


@app.post("/auth/register")
def register_user(request: RegisterRequest):
    """
    Real user registration -- creates an account with a properly hashed
    password. Added after real user feedback that the system needed a way
    for staff to register themselves, rather than only having one seeded
    demo account. Extended to also cover 'patient' (submits their own
    intake) and 'doctor' (attends assigned patients) for the review
    workflow.

    HONEST SECURITY NOTE: role is currently self-selected at signup with
    no approval step for ANY role, including 'admin' and 'doctor' -- fine
    for a final year project demo, but a real deployment would never let
    a new account grant itself admin or doctor access; 'doctor' in
    particular should require verification in a real system. Flagged
    here, not hidden -- same honest tradeoff already made for 'admin'
    before this change, now consistently applied to 'doctor' too rather
    than building a separate admin-only doctor-creation flow this close
    to a defense deadline.
    """
    if request.role not in ("clinician", "admin", "patient", "doctor"):
        raise HTTPException(status_code=400, detail="Role must be 'clinician', 'admin', 'patient', or 'doctor'")
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    try:
        result = register(request.username, request.password, role_name=request.role, email=request.email)
    except UsernameTaken as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )

    # Best-effort, own try/except: registration has already succeeded by
    # here, so a verification-email failure must never undo the account
    # or fail this response -- the user can always use "Resend code" later.
    email_verification_sent = False
    if request.email:
        try:
            code = generate_verification_code(request.email)
            if code:
                email_verification_sent = send_verification_email(request.email, code)
        except Exception as e:
            print(f"[notifications] Could not send verification email to {request.email}: {type(e).__name__}: {e}")

    return {
        "status": "ok", "user_id": result["user_id"], "role": result["role"],
        "email_verification_sent": email_verification_sent,
    }


@app.post("/auth/verify-email")
def verify_email_endpoint(request: VerifyEmailRequest):
    try:
        success = verify_email(request.email, request.code)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )
    if not success:
        raise HTTPException(status_code=400, detail="That code is incorrect, expired, or already used.")
    return {"status": "ok"}


@app.post("/auth/resend-verification")
def resend_verification(request: ResendVerificationRequest):
    """
    Same generic-response pattern as forgot-password: always returns ok
    so this can't be used to check which emails are registered/verified.
    """
    try:
        code = generate_verification_code(request.email)
        if code:
            send_verification_email(request.email, code)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )
    return {"status": "ok", "message": "If that email needs verifying, a new code has been sent."}


@app.post("/auth/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    """
    Always returns the same generic message whether or not the email
    matches an account -- deliberately, so this endpoint can't be used to
    check which emails are registered. If it does match, a reset email is
    sent (best-effort: if Brevo is unreachable or unconfigured, this
    still returns success rather than leaking that distinction either).
    """
    try:
        token = create_password_reset_token(request.email)
        if token:
            send_password_reset_email(request.email, token)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )
    return {"status": "ok", "message": "If that email is registered, a reset link has been sent."}


@app.post("/auth/reset-password")
def reset_password(request: ResetPasswordRequest):
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    try:
        success = reset_password_with_token(request.token, request.new_password)
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )
    if not success:
        raise HTTPException(status_code=400, detail="This reset link is invalid or has expired.")
    return {"status": "ok"}


@app.post("/vision-check")
async def vision_check(image: UploadFile = File(...)):
    """
    Module 5.1-5.3 - Upload a skin-condition image, get back the redness/
    inflammation analysis. Call this FIRST if you have an image, then pass
    the returned 'flag' value as has_vision_red_flag in your /triage
    request. Kept as a separate endpoint from /triage since file uploads
    and JSON bodies don't mix cleanly in one request.

    HONEST LIMITATION (also in vision_agent.py): this is an uncalibrated
    heuristic, not a trained clinical classifier -- see that file's
    docstring for a documented case where it over-flags pale pink tones.
    """
    contents = await image.read()
    pil_image = Image.open(io.BytesIO(contents))
    result = inflammation_score(pil_image)
    flag = vision_flag_for_triage(result)

    return {
        "analysis": result,
        "flag": flag,
        "note": "Heuristic redness-index scoring, not a trained clinical "
                "classifier -- correlate with clinical exam.",
    }


@app.post("/triage")
def triage(request: TriageRequest):
    patient = PatientInput(
        symptoms=set(request.symptoms),
        temperature=request.temperature,
        heart_rate=request.heart_rate,
        respiratory_rate=request.respiratory_rate,
        systolic=request.systolic,
        diastolic=request.diastolic,
        spo2=request.spo2,
        age_years=request.age_years,
        has_vision_red_flag=request.has_vision_red_flag,
    )

    result = run_pipeline(patient, chat_message=request.chat_message)

    # Persist to the database, but NEVER let a persistence failure break
    # the triage response itself -- same error-isolation philosophy as
    # the agent orchestrator. If the DB is down, the clinician still gets
    # their triage result; it just won't show up on the dashboard later.
    persistence_error = None
    if result.triage_output is not None:
        try:
            pseudonym = request.patient_pseudonym or f"PT-{uuid.uuid4().hex[:8].upper()}"
            persist_triage_decision(
                patient_pseudonym=pseudonym,
                age_years=request.age_years,
                vitals={
                    "temperature": request.temperature, "heart_rate": request.heart_rate,
                    "respiratory_rate": request.respiratory_rate, "systolic": request.systolic,
                    "diastolic": request.diastolic, "spo2": request.spo2,
                },
                symptoms=request.symptoms,
                triage_output=result.triage_output,
                status="pending_review" if request.self_submitted else "finalized",
                patient_user_id=request.submitted_by_user_id if request.self_submitted else None,
            )
        except Exception as e:
            persistence_error = f"{type(e).__name__}: {e}"

    errors = dict(result.errors) if result.had_partial_failure else {}
    if persistence_error:
        errors["persistence"] = persistence_error

    return {
        "triage": result.triage_output,
        "interaction_check": result.interaction_output,
        "chat_response": result.chat_output,
        "partial_failures": errors if errors else None,
    }


@app.get("/admin/users")
def list_users():
    """
    Real registered-user list, for the Admin page. HONEST SECURITY NOTE:
    this endpoint is NOT actually access-controlled at the API level --
    there's no session/token system yet (see auth.py), so this relies
    entirely on the frontend hiding the Admin nav link for non-admin
    users, which a determined user could bypass by calling this URL
    directly. Flagged clearly as a known limitation, not silently ignored.
    Real protection requires the token-based auth described in auth.py's
    docstring as the natural next step.
    """
    try:
        return {"users": get_all_users()}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )


@app.get("/encounters/recent")
def recent_encounters(limit: int = 20):
    """
    Real recent-decisions feed for the dashboard -- closes the gap
    flagged in Phase 7, where a dashboard would have had no real data
    since nothing was being persisted.
    """
    try:
        return {"encounters": get_recent_decisions(limit)}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )


# --- Review workflow: patient submits -> admin reviews -> doctor attends ---
#
# HONEST SECURITY NOTE (same limitation already flagged on /admin/users):
# none of these endpoints are actually access-controlled server-side --
# there's no session/token system yet (see auth.py's docstring). They
# rely on the frontend only showing the relevant dashboard/actions to the
# right role, and on the *_user_id fields being supplied honestly by the
# client (itself only trustworthy as far as localStorage goes). A real
# deployment needs server-issued sessions checked on every request here --
# noted as a known limitation for the defense Q&A, not silently ignored.

@app.get("/admin/dashboard-stats")
def admin_dashboard_stats():
    """
    Everything the Admin dashboard's cards/charts/activity feed need in
    one call: real counts, a real diagnosis breakdown, a 7-day trend, and
    a genuine recent-activity feed built from real status changes.
    Deliberately does NOT include hospital-ops numbers this system has
    no real data for (revenue, appointments, department popularity) --
    same principle as the rest of this dashboard.
    """
    try:
        return get_admin_dashboard_stats()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )


@app.get("/admin/pending")
def pending_reviews():
    """Patient self-submissions awaiting admin approval/rejection."""
    try:
        return {"pending": get_pending_decisions()}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )


@app.get("/admin/doctors/available")
def available_doctors():
    """Doctors an admin can assign a just-approved case to."""
    try:
        return {"doctors": get_available_doctors()}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )


@app.post("/admin/decisions/{decision_id}/approve")
def approve(decision_id: int, request: ApproveRequest):
    try:
        approve_decision(decision_id, request.doctor_id, request.admin_user_id)
    except DecisionNotPending as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )

    # Best-effort: a notification failure must never undo or fail the
    # approval itself, which is why this is its own try/except separate
    # from the block above -- the approval has already succeeded by now.
    try:
        info = get_decision_notification_info(decision_id)
        if info:
            send_approval_notification(info["patient_email"], info["tier"], info["doctor_username"])
    except Exception as e:
        print(f"[notifications] Could not send approval email for decision {decision_id}: {type(e).__name__}: {e}")

    return {"status": "ok"}


@app.post("/admin/decisions/{decision_id}/reject")
def reject(decision_id: int, request: RejectRequest):
    try:
        reject_decision(decision_id, request.admin_user_id, request.reason)
    except DecisionNotPending as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )
    return {"status": "ok"}


@app.get("/doctor/assigned")
def assigned_to_doctor(doctor_id: int):
    """Cases assigned to this doctor, for their own dashboard."""
    try:
        return {"assigned": get_assigned_decisions(doctor_id)}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )


@app.post("/doctor/decisions/{decision_id}/attend")
def attend(decision_id: int, request: AttendRequest):
    try:
        mark_attended(decision_id, request.doctor_id)
    except NotAssignedToDoctor as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )
    return {"status": "ok"}


@app.get("/patient/history")
def patient_history(patient_user_id: int):
    """A logged-in patient's own past submissions and their status."""
    try:
        return {"history": get_patient_history(patient_user_id)}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach database: {type(e).__name__}: {e}",
        )


# --- Single-server mode: serve the built frontend directly ---
# After `npm run build` in frontend/, this serves the whole app (login,
# intake, dashboard, result) from THIS same FastAPI server/port -- one
# process, one terminal, no separate frontend dev server, no proxy.
# MUST be registered LAST so it doesn't swallow the API routes above --
# FastAPI matches routes in registration order, and the catch-all below
# would otherwise intercept every request, including /triage etc.
#
# HONEST STATUS: written carefully, NOT runtime-tested here (no
# `npm run build` output exists in this sandbox to serve). First real
# test happens on your machine -- see docs/SETUP.md "Running as ONE
# server" section.
_FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")

if os.path.isdir(_FRONTEND_DIST):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    _assets_dir = os.path.join(_FRONTEND_DIST, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        """
        SPA fallback: React Router handles routes like /intake, /result,
        /dashboard entirely client-side, so any of these must still
        receive index.html (React then reads the URL and renders the
        right page) rather than a 404.
        """
        return FileResponse(os.path.join(_FRONTEND_DIST, "index.html"))
else:
    @app.get("/")
    def frontend_not_built():
        """
        Self-diagnosing fallback: if frontend/dist doesn't exist, say so
        explicitly instead of a bare, unhelpful 404 -- this exact
        confusion (silent 404 with no clue why) came up in real testing.
        """
        return {
            "detail": "Frontend not built yet.",
            "fix": "Run 'npm run build' inside the frontend/ folder, "
                   "then restart this server (Ctrl+C, then uvicorn "
                   "main:app --reload --port 8000 again).",
            "expected_path_checked": _FRONTEND_DIST,
        }
