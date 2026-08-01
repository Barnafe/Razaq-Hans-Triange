import React from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'

const clinicianNavItems = [
  { to: '/dashboard', label: 'Dashboard', icon: <DashboardIcon /> },
  { to: '/intake', label: 'New Assessment', icon: <PlusIcon /> },
]
const patientNavItems = [
  { to: '/dashboard/patient', label: 'My Profile', icon: <DashboardIcon /> },
]
const doctorNavItems = [
  { to: '/dashboard/doctor', label: 'Clinical', icon: <DashboardIcon /> },
]
const adminNavItems = [
  { to: '/admin', label: 'Admin', icon: <ShieldIcon /> },
  { to: '/dashboard', label: 'All Assessments', icon: <DashboardIcon /> },
]

export default function Layout() {
  const navigate = useNavigate()
  const role = localStorage.getItem('hans_triage_role')
  const items =
    role === 'admin' ? adminNavItems :
    role === 'patient' ? patientNavItems :
    role === 'doctor' ? doctorNavItems :
    clinicianNavItems

  function handleLogout() {
    // HONEST NOTE: no real session/token exists yet to invalidate server-
    // side (see backend/app/db/auth.py docstring) -- this clears the
    // locally-stored identity and navigates back to login.
    localStorage.removeItem('hans_triage_role')
    localStorage.removeItem('hans_triage_user_id')
    localStorage.removeItem('hans_triage_username')
    navigate('/')
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside
        style={{
          width: 240,
          background: 'var(--color-sidebar-bg)',
          color: 'var(--color-sidebar-text)',
          padding: 'var(--space-6) var(--space-4)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-8)',
        }}
      >
        <div>
          <div
            style={{
              fontFamily: 'var(--font-display)',
              fontWeight: 700,
              fontSize: 20,
              color: '#FFFFFF',
              letterSpacing: '-0.02em',
            }}
          >
            HANS<span style={{ color: 'var(--color-teal)' }}>-</span>Triage
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-sidebar-text)', marginTop: 4 }}>
            Clinical Decision Support
          </div>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', flex: 1 }}>
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              style={({ isActive }) => ({
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '10px 12px',
                borderRadius: 'var(--radius-sm)',
                textDecoration: 'none',
                color: isActive ? 'var(--color-sidebar-text-active)' : 'var(--color-sidebar-text)',
                background: isActive ? 'rgba(14, 124, 134, 0.35)' : 'transparent',
                fontSize: 14,
                fontWeight: 500,
                transition: 'background 0.15s ease',
              })}
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </nav>

        <button
          onClick={handleLogout}
          style={{
            display: 'flex', alignItems: 'center', gap: 10,
            background: 'none', border: '1px solid #2A3A47', color: 'var(--color-sidebar-text)',
            borderRadius: 'var(--radius-sm)', padding: '10px 12px', fontSize: 14, cursor: 'pointer',
            textAlign: 'left',
          }}
        >
          <LogoutIcon /> Log out
        </button>

        <div style={{ fontSize: 11, color: '#5A6B7A', lineHeight: 1.5 }}>
          Disease Symptom-Based Triage &amp; Clinical Decision Support System
          <br />
          Final Year Project — ATBU Bauchi
        </div>
      </aside>

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div
          style={{
            background: 'var(--tier-yellow-bg)', borderBottom: '1px solid var(--tier-yellow)',
            padding: '8px 24px', fontSize: 12, color: '#7C5E00', fontWeight: 500,
          }}
        >
          ⚠ This system provides advisory decision support only and is not a replacement for clinical judgment. All recommendations must be verified by a qualified healthcare professional.
        </div>
        <div style={{ padding: 'var(--space-8)', flex: 1, background: 'var(--color-bg)' }}>
          <Outlet />
        </div>
      </main>
    </div>
  )
}

function DashboardIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="3" width="7" height="9" rx="1" /><rect x="14" y="3" width="7" height="5" rx="1" />
      <rect x="14" y="12" width="7" height="9" rx="1" /><rect x="3" y="16" width="7" height="5" rx="1" />
    </svg>
  )
}
function PlusIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="9" /><line x1="12" y1="8" x2="12" y2="16" /><line x1="8" y1="12" x2="16" y2="12" />
    </svg>
  )
}
function ShieldIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6z" />
    </svg>
  )
}
function LogoutIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  )
}
