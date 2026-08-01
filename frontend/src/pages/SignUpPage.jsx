import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { register } from '../api/client'

// Real registration page -- added after user feedback that the system
// needed a way for staff to create accounts, not just one seeded demo
// user. Matches the login page's visual style for consistency.

export default function SignUpPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [role, setRole] = useState('clinician')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
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
      await register(username, password, role)
      setSuccess(true)
      setTimeout(() => navigate('/'), 1500)
    } catch (err) {
      setError(err.message || 'Registration failed.')
    } finally {
      setLoading(false)
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
        <h1 style={{ textAlign: 'center', fontSize: 24, marginBottom: 'var(--space-2)' }}>
          Create Account
        </h1>
        <p style={{ textAlign: 'center', fontSize: 13, color: 'var(--color-ink-muted)', marginBottom: 'var(--space-8)' }}>
          Register as a clinician to use HANS-Triage
        </p>

        {success ? (
          <div style={{ textAlign: 'center', color: 'var(--tier-green)', fontSize: 14 }}>
            Account created! Redirecting to sign in…
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <Field label="Username">
              <input value={username} onChange={(e) => setUsername(e.target.value)} style={inputStyle} required />
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
        )}

        <div style={{ textAlign: 'center', fontSize: 12, marginTop: 'var(--space-6)', color: 'var(--color-ink-muted)' }}>
          Already have an account? <Link to="/" style={{ color: 'var(--color-teal)', fontWeight: 600 }}>Sign In</Link>
        </div>
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
