import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { forgotPassword } from '../api/client'

// Matches LoginPage/SignUpPage's card style for visual consistency.
// Deliberately always shows the same success message regardless of
// whether the email is registered -- the backend does the same (see
// /auth/forgot-password's docstring) so this page can't be used to
// enumerate which emails have accounts.

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await forgotPassword(email)
      setSent(true)
    } catch (err) {
      setError(err.message || 'Something went wrong.')
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
          Forgot Password?
        </h1>
        <p style={{ textAlign: 'center', fontSize: 13, color: 'var(--color-ink-muted)', marginBottom: 'var(--space-8)' }}>
          Enter the email on your account and we'll send you a reset link.
        </p>

        {sent ? (
          <div style={{ textAlign: 'center', color: 'var(--tier-green)', fontSize: 14 }}>
            If that email is registered, a reset link is on its way. Check your inbox
            (and spam folder) — the link expires in 1 hour.
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-teal)' }}>Email</span>
              <input
                type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                style={inputStyle} placeholder="you@example.com" required
              />
            </label>

            {error && <div style={{ fontSize: 12, color: 'var(--tier-red)' }}>{error}</div>}

            <button type="submit" disabled={loading} style={submitButtonStyle}>
              {loading ? 'Sending…' : 'Send Reset Link'}
            </button>
          </form>
        )}

        <div style={{ textAlign: 'center', fontSize: 12, marginTop: 'var(--space-6)', color: 'var(--color-ink-muted)' }}>
          <Link to="/" style={{ color: 'var(--color-teal)', fontWeight: 600 }}>Back to Sign In</Link>
        </div>
      </div>
    </div>
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
