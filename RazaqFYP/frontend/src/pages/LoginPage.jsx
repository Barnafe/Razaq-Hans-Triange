import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { login } from '../api/client'

// Rebuilt to closely match the supervisor's actual reference design:
// teal gradient bg, decorative icon circles, white card, "Welcome Back!"
// heading, email/phone + password fields, Google sign-in, EKG line motif.
//
// Now wired to REAL authentication (backend/app/db/auth.py) -- a wrong
// password genuinely fails. HONEST SCOPE NOTE: no session/token is
// issued or stored after login -- see auth.py's docstring for what a
// production version would add. The "Continue with Google" button
// remains visual only, not connected to real OAuth.

export default function LoginPage() {
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [googleMessage, setGoogleMessage] = useState(null)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const result = await login(identifier, password)
      // HONEST NOTE: this is client-side-only identity storage, not a
      // real session/token -- see auth.py's docstring. Good enough to
      // drive which nav links show and which user_id gets sent with
      // requests that need one (submitting as a patient, approving as
      // an admin, attending as a doctor). NOT a real access-control
      // boundary -- the API endpoints themselves aren't protected by
      // this, and anyone could edit these values directly. Flagged
      // clearly for the defense Q&A, not hidden.
      localStorage.setItem('hans_triage_role', result.role)
      localStorage.setItem('hans_triage_user_id', String(result.user_id))
      localStorage.setItem('hans_triage_username', identifier)
      if (result.role === 'patient') navigate('/dashboard/patient')
      else if (result.role === 'doctor') navigate('/dashboard/doctor')
      else if (result.role === 'admin') navigate('/admin')
      else navigate('/intake')
    } catch (err) {
      setError(err.message || 'Login failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        position: 'relative',
        overflow: 'hidden',
        display: 'grid',
        placeItems: 'center',
        background: 'linear-gradient(160deg, var(--color-teal-dark), var(--color-teal))',
      }}
    >
      <IconCircle top={40} left="50%" style={{ transform: 'translateX(-50%)' }} size={90}>
        <HeartIcon />
      </IconCircle>
      <IconCircle top="35%" left={60} size={200}>
        <DnaIcon />
      </IconCircle>
      <IconCircle top="45%" right={40} size={230}>
        <StethoscopeIcon />
      </IconCircle>

      <svg
        style={{ position: 'absolute', bottom: 60, left: 0, width: '100%', opacity: 0.35 }}
        height="60" viewBox="0 0 1600 60" preserveAspectRatio="none"
      >
        <polyline
          points="0,30 300,30 340,10 370,50 400,30 700,30 740,10 770,50 800,30 1100,30 1140,10 1170,50 1200,30 1600,30"
          fill="none" stroke="white" strokeWidth="2"
        />
      </svg>

      <div
        style={{
          background: 'var(--color-surface)',
          borderRadius: 20,
          padding: 'var(--space-12) var(--space-8)',
          width: 400,
          position: 'relative',
          boxShadow: '0 24px 70px rgba(10, 40, 44, 0.3)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 'var(--space-4)' }}>
          <LogoIcon />
        </div>

        <h1 style={{ textAlign: 'center', fontSize: 24, marginBottom: 'var(--space-8)' }}>
          Welcome Back!
        </h1>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          <Field label="Email or No. Handphone" icon={<PersonIcon />}>
            <input
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              placeholder="you@example.com"
              style={inputStyle}
              required
            />
          </Field>

          <Field
            label="Password"
            icon={
              <button
                type="button"
                onClick={() => setShowPassword((s) => !s)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                <EyeIcon open={showPassword} />
              </button>
            }
          >
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={inputStyle}
              required
            />
          </Field>

          <div style={{ textAlign: 'right', marginTop: -6 }}>
            <a href="#" style={{ fontSize: 12, color: 'var(--color-teal)', textDecoration: 'none' }}>
              Forgot Password?
            </a>
          </div>

          {error && (
            <div style={{ fontSize: 12, color: 'var(--tier-red)', textAlign: 'center' }}>{error}</div>
          )}

          <button type="submit" disabled={loading} style={signInButtonStyle}>
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: 'var(--space-6) 0' }}>
          <div style={{ flex: 1, height: 1, background: 'var(--color-border)' }} />
          <span style={{ fontSize: 11, color: 'var(--color-ink-muted)' }}>OR</span>
          <div style={{ flex: 1, height: 1, background: 'var(--color-border)' }} />
        </div>

        <button
          type="button"
          onClick={() => setGoogleMessage('Google sign-in requires a registered OAuth app (Google Cloud project) — not set up in this build. Use the form above instead.')}
          style={googleButtonStyle}
        >
          <GoogleIcon /> Continue with Google
        </button>
        {googleMessage && (
          <div style={{ fontSize: 11, color: 'var(--color-ink-muted)', marginTop: 8, textAlign: 'center' }}>
            {googleMessage}
          </div>
        )}

        <div style={{ textAlign: 'center', fontSize: 12, marginTop: 'var(--space-4)', color: 'var(--color-ink-muted)' }}>
          Don't have an account? <Link to="/signup" style={{ color: 'var(--color-teal)', fontWeight: 600 }}>Sign Up</Link>
        </div>

        <div style={{ marginTop: 'var(--space-4)', fontSize: 10, color: 'var(--color-ink-muted)', textAlign: 'center' }}>
          Demo credentials: nurse_amina / TriageDemo2026! (see scripts/seed_demo_user.py)
        </div>
      </div>
    </div>
  )
}

function IconCircle({ top, left, right, size, children, style }) {
  return (
    <div
      style={{
        position: 'absolute', top, left, right, width: size, height: size,
        borderRadius: '50%', background: 'rgba(255,255,255,0.1)',
        display: 'grid', placeItems: 'center', ...style,
      }}
    >
      {children}
    </div>
  )
}

function Field({ label, icon, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-teal)' }}>{label}</span>
      <div style={{ display: 'flex', alignItems: 'center', borderBottom: '1px solid var(--color-border)', paddingBottom: 6 }}>
        <div style={{ flex: 1 }}>{children}</div>
        <div style={{ color: 'var(--color-ink-muted)' }}>{icon}</div>
      </div>
    </label>
  )
}

const inputStyle = {
  border: 'none', outline: 'none', fontSize: 14, width: '100%',
  fontFamily: 'var(--font-body)', background: 'transparent',
}

const signInButtonStyle = {
  marginTop: 'var(--space-2)', background: 'var(--color-teal)', color: 'white',
  border: 'none', borderRadius: 999, padding: '13px', fontWeight: 600, fontSize: 14,
}

const googleButtonStyle = {
  width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
  background: 'white', border: '1px solid var(--color-border)', borderRadius: 999,
  padding: '11px', fontWeight: 500, fontSize: 13, color: 'var(--color-ink)',
}

function LogoIcon() {
  return (
    <svg width="44" height="44" viewBox="0 0 44 44" fill="none">
      <rect x="18" y="4" width="8" height="36" rx="4" fill="var(--color-teal)" />
      <rect x="4" y="18" width="36" height="8" rx="4" fill="var(--color-teal)" />
      <circle cx="34" cy="10" r="3" fill="var(--color-teal-dark)" />
    </svg>
  )
}

function PersonIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 20c0-4.4 3.6-8 8-8s8 3.6 8 8" />
    </svg>
  )
}

function EyeIcon({ open }) {
  return open ? (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ) : (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M17.9 17.9A10.9 10.9 0 0 1 12 20c-7 0-11-8-11-8a19.5 19.5 0 0 1 5-5.6M9.9 4.2A10 10 0 0 1 12 4c7 0 11 8 11 8a19.6 19.6 0 0 1-2.2 3.1M14.1 14.1a3 3 0 1 1-4.2-4.2" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  )
}

function GoogleIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.4H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.6v3h3.9c2.3-2.1 3.5-5.2 3.5-8.7z" />
      <path fill="#34A853" d="M12 24c3.2 0 5.9-1.1 7.9-2.9l-3.9-3c-1.1.7-2.4 1.1-4 1.1-3.1 0-5.7-2.1-6.6-4.9H1.4v3.1C3.4 21.3 7.4 24 12 24z" />
      <path fill="#FBBC05" d="M5.4 14.3c-.2-.7-.4-1.5-.4-2.3s.1-1.6.4-2.3V6.6H1.4A12 12 0 0 0 0 12c0 1.9.5 3.8 1.4 5.4z" />
      <path fill="#EA4335" d="M12 4.8c1.7 0 3.3.6 4.5 1.7l3.4-3.4C17.9 1.2 15.2 0 12 0 7.4 0 3.4 2.7 1.4 6.6l4 3.1c.9-2.8 3.5-4.9 6.6-4.9z" />
    </svg>
  )
}

function DnaIcon() {
  return (
    <svg width="60%" height="60%" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" opacity="0.8">
      <path d="M6 3c0 6 12 6 12 12M6 21c0-6 12-6 12-12" />
      <line x1="8" y1="6" x2="16" y2="6" />
      <line x1="9" y1="10" x2="15" y2="10" />
      <line x1="9" y1="14" x2="15" y2="14" />
      <line x1="8" y1="18" x2="16" y2="18" />
    </svg>
  )
}

function StethoscopeIcon() {
  return (
    <svg width="55%" height="55%" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" opacity="0.8">
      <path d="M4 4v5a4 4 0 0 0 8 0V4M4 4H2.5M12 4h1.5" />
      <path d="M12 9v3a6 6 0 0 0 12 0v-1" />
      <circle cx="22" cy="9" r="1.6" />
    </svg>
  )
}

function HeartIcon() {
  return (
    <svg width="50%" height="50%" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="1.5" opacity="0.85">
      <path d="M12 21s-7-4.6-9.5-9C.6 8.4 2 4.5 5.6 3.7 8 3.2 10.3 4.4 12 7c1.7-2.6 4-3.8 6.4-3.3C22 4.5 23.4 8.4 21.5 12 19 16.4 12 21 12 21z" />
    </svg>
  )
}
