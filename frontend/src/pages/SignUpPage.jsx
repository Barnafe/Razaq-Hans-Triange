import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register, verifyEmail, resendVerification } from '../api/client'

// Real registration page -- added after user feedback that the system
// needed a way for staff to create accounts, not just one seeded demo
// user. Matches the login page's visual style for consistency.
//
// Three stages: 'form' (fill in details) -> 'verify' (enter the emailed
// code -- only reached if an email was given and sending succeeded) ->
// 'done'. If no email was given, or sending failed, we skip straight to
// 'done' -- verification is a bonus on top of a working account, never
// a blocker to actually using it.

export default function SignUpPage() {
  const [stage, setStage] = useState('form')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [role, setRole] = useState('clinician')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const [code, setCode] = useState('')
  const [verifyError, setVerifyError] = useState(null)
  const [verifyLoading, setVerifyLoading] = useState(false)
  const [resendMessage, setResendMessage] = useState(null)

  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)

    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      const result = await register(username, password, role, email || null)
      if (email && result.email_verification_sent) {
        setStage('verify')
      } else {
        setStage('done')
        setTimeout(() => navigate('/'), 1500)
      }
    } catch (err) {
      setError(err.message || 'Registration failed.')
    } finally {
      setLoading(false)
    }
  }

  async function handleVerify(e) {
    e.preventDefault()
    setVerifyError(null)
    setVerifyLoading(true)
    try {
      await verifyEmail(email, code)
      setStage('done')
      setTimeout(() => navigate('/'), 1500)
    } catch (err) {
      setVerifyError(err.message || 'Verification failed.')
    } finally {
      setVerifyLoading(false)
    }
  }

  async function handleResend() {
    setResendMessage(null)
    try {
      await resendVerification(email)
      setResendMessage('A new code has been sent.')
    } catch (err) {
      setResendMessage(err.message || 'Could not resend code.')
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh', display: 'grid', placeItems: 'center',
        background: 'linear-gradient(160deg, var(--color-teal-dark), var(--color-teal))',
      }}
    >
      <div
        style={{
          background: 'var(--color-surface)', borderRadius: 20,
          padding: 'var(--space-12) var(--space-8)', width: 400,
          boxShadow: '0 24px 70px rgba(10, 40, 44, 0.3)',
        }}
      >
        {stage === 'form' && (
          <>
            <h1 style={{ textAlign: 'center', fontSize: 24, marginBottom: 'var(--space-2)' }}>
              Create Account
            </h1>
            <p style={{ textAlign: 'center', fontSize: 13, color: 'var(--color-ink-muted)', marginBottom: 'var(--space-8)' }}>
              Register as a clinician to use HANS-Triage
            </p>

            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <Field label="Username">
                <input value={username} onChange={(e) => setUsername(e.target.value)} style={inputStyle} required />
              </Field>
              <Field label="Email">
                <input
                  type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  style={inputStyle} placeholder="you@example.com"
                />
                <span style={{ fontSize: 11, color: 'var(--color-ink-muted)' }}>
                  Optional, but needed for "Forgot Password" and (for patients)
                  email alerts when your assessment is approved. If given,
                  you'll be asked to confirm it with a code before you're done.
                </span>
              </Field>
              <Field label="Password">
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} style={inputStyle} required />
              </Field>
              <Field label="Confirm Password">
                <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} style={inputStyle} required />
              </Field>
              <Field label="Account Type">
                <select value={role} onChange={(e) => setRole(e.target.value)} style={inputStyle}>
                  <option value="clinician">Clinician</option>
                  <option value="patient">Patient</option>
                  <option value="doctor">Doctor</option>
                  <option value="admin">Admin</option>
                </select>
                <span style={{ fontSize: 11, color: 'var(--color-ink-muted)' }}>
                  Demo build: role is self-selected here, no approval step
                  (a real deployment would never let Doctor/Admin self-grant
                  like this — flagged, not hidden).
                </span>
              </Field>

              {error && <div style={{ fontSize: 12, color: 'var(--tier-red)' }}>{error}</div>}

              <button type="submit" disabled={loading} style={submitButtonStyle}>
                {loading ? 'Creating account…' : 'Create Account'}
              </button>
            </form>

            <div style={{ textAlign: 'center', fontSize: 12, marginTop: 'var(--space-6)', color: 'var(--color-ink-muted)' }}>
              Already have an account? <Link to="/" style={{ color: 'var(--color-teal)', fontWeight: 600 }}>Sign In</Link>
            </div>
          </>
        )}

        {stage === 'verify' && (
          <>
            <h1 style={{ textAlign: 'center', fontSize: 24, marginBottom: 'var(--space-2)' }}>
              Verify Your Email
            </h1>
            <p style={{ textAlign: 'center', fontSize: 13, color: 'var(--color-ink-muted)', marginBottom: 'var(--space-8)' }}>
              We sent a 6-digit code to <strong>{email}</strong>. Enter it below to confirm.
            </p>

            <form onSubmit={handleVerify} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              <Field label="Verification Code">
                <input
                  value={code} onChange={(e) => setCode(e.target.value)}
                  style={{ ...inputStyle, textAlign: 'center', fontSize: 22, letterSpacing: 6 }}
                  placeholder="000000" maxLength={6} required
                />
              </Field>

              {verifyError && <div style={{ fontSize: 12, color: 'var(--tier-red)' }}>{verifyError}</div>}

              <button type="submit" disabled={verifyLoading} style={submitButtonStyle}>
                {verifyLoading ? 'Verifying…' : 'Verify Email'}
              </button>
            </form>

            <div style={{ textAlign: 'center', fontSize: 12, marginTop: 'var(--space-6)', color: 'var(--color-ink-muted)' }}>
              Didn't get it?{' '}
              <button
                type="button" onClick={handleResend}
                style={{ background: 'none', border: 'none', color: 'var(--color-teal)', fontWeight: 600, cursor: 'pointer', padding: 0 }}
              >
                Resend code
              </button>
              {resendMessage && <div style={{ marginTop: 6 }}>{resendMessage}</div>}
            </div>
            <div style={{ textAlign: 'center', fontSize: 12, marginTop: 'var(--space-3)' }}>
              <Link to="/" style={{ color: 'var(--color-ink-muted)' }}>Skip for now, sign in later</Link>
            </div>
          </>
        )}

        {stage === 'done' && (
          <div style={{ textAlign: 'center', color: 'var(--tier-green)', fontSize: 14 }}>
            Account ready! Redirecting to sign in…
          </div>
        )}
      </div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-teal)' }}>{label}</span>
      {children}
    </label>
  )
}

const inputStyle = {
  padding: '10px 12px', borderRadius: 'var(--radius-sm)',
  border: '1px solid var(--color-border)', fontSize: 14, fontFamily: 'var(--font-body)',
}
const submitButtonStyle = {
  marginTop: 'var(--space-2)', background: 'var(--color-teal)', color: 'white',
  border: 'none', borderRadius: 999, padding: '13px', fontWeight: 600, fontSize: 14,
}

