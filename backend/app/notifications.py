"""
Email notifications via Brevo's transactional email HTTP API.

Uses Brevo's REST API over plain HTTPS rather than SMTP, because Render's
free tier blocks outbound SMTP ports (25/465/587) -- HTTPS works fine.

HONEST SCOPE NOTE: email sending is treated as best-effort everywhere it's
called. If BREVO_API_KEY is missing, misconfigured, or Brevo's API is
unreachable, these functions log the failure and return False rather than
raising. Registration, login, and the admin approval workflow must keep
working even if email delivery is broken -- a notification failure should
never block the core clinical workflow.
"""
import os
import requests

BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
# Must be a sender address/domain you've verified in your Brevo account --
# Brevo rejects sends from an unverified sender.
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "no-reply@hans-triage.example")
BREVO_SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "HANS-Triage")
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

# Where the frontend is actually served -- used to build the link inside
# the password reset email. Set this on Render to your real onrender.com
# URL; falls back to the local Vite dev server for local testing.
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:5173")


def _send(to_email: str, subject: str, html_content: str) -> bool:
    if not BREVO_API_KEY:
        print(f"[notifications] BREVO_API_KEY not set -- skipping email to {to_email}: {subject!r}")
        return False
    try:
        response = requests.post(
            BREVO_API_URL,
            headers={
                "api-key": BREVO_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "sender": {"name": BREVO_SENDER_NAME, "email": BREVO_SENDER_EMAIL},
                "to": [{"email": to_email}],
                "subject": subject,
                "htmlContent": html_content,
            },
            timeout=10,
        )
        if response.status_code >= 300:
            print(f"[notifications] Brevo API error {response.status_code} sending to {to_email}: {response.text}")
            return False
        return True
    except Exception as e:
        print(f"[notifications] Failed to send email to {to_email}: {type(e).__name__}: {e}")
        return False


def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    reset_link = f"{APP_BASE_URL}/reset-password?token={reset_token}"
    html = f"""
        <div style="font-family: sans-serif; max-width: 480px;">
            <h2 style="color: #1a6b6b;">Reset your HANS-Triage password</h2>
            <p>We received a request to reset the password for your account.</p>
            <p>
                <a href="{reset_link}"
                   style="background:#1a6b6b;color:#fff;padding:10px 20px;
                          border-radius:6px;text-decoration:none;display:inline-block;">
                    Reset Password
                </a>
            </p>
            <p style="color:#666;font-size:13px;">
                This link expires in 1 hour. If you didn't request this, you can
                safely ignore this email -- your password will not be changed.
            </p>
        </div>
    """
    return _send(to_email, "Reset your HANS-Triage password", html)


def send_verification_email(to_email: str, code: str) -> bool:
    html = f"""
        <div style="font-family: sans-serif; max-width: 480px;">
            <h2 style="color: #1a6b6b;">Verify your HANS-Triage email</h2>
            <p>Enter this code on the verification screen to confirm this is your email:</p>
            <p style="font-size: 32px; font-weight: 700; letter-spacing: 6px; color: #1a6b6b; margin: 20px 0;">
                {code}
            </p>
            <p style="color:#666;font-size:13px;">
                This code expires in 15 minutes. Verifying your email means it can be trusted
                for password recovery and assessment-approval alerts.
            </p>
        </div>
    """
    return _send(to_email, "Verify your HANS-Triage email", html)


def send_approval_notification(to_email: str, tier: str, doctor_username: str) -> bool:
    html = f"""
        <div style="font-family: sans-serif; max-width: 480px;">
            <h2 style="color: #1a6b6b;">Your assessment has been reviewed</h2>
            <p>Your recent HANS-Triage assessment has been approved and assigned to a doctor.</p>
            <table style="margin: 16px 0;">
                <tr><td style="padding:4px 12px 4px 0;color:#666;">Urgency tier</td><td><strong>{tier}</strong></td></tr>
                <tr><td style="padding:4px 12px 4px 0;color:#666;">Assigned doctor</td><td><strong>{doctor_username}</strong></td></tr>
            </table>
            <p>Log in to your patient dashboard to see full details.</p>
            <p style="color:#999;font-size:12px;">
                This is advisory decision support only, not a replacement for
                clinical judgment.
            </p>
        </div>
    """
    return _send(to_email, "Your HANS-Triage assessment has been approved", html)
