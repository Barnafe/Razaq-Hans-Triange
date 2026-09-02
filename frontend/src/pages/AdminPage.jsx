import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import {
  getAllUsers, getAdminDashboardStats, getPendingReviews,
  getAvailableDoctors, approveDecision, rejectDecision,
} from '../api/client'

// Redesigned to match the supervisor's MediSys admin dashboard
// reference -- including a dark theme, scoped to just this page (not
// the whole app, so Patient/Doctor/Clinician pages keep their own
// light branding) via a CSS-custom-property override on the wrapper
// div below. Every number here is real. Deliberately does NOT show
// hospital-ops metrics (revenue, appointments, billing, department
// popularity) -- this system has no real data source for those, and
// does not fake them. "Diagnosis Breakdown" replaces "Department
// Popularity" (both donuts; ours is real), "Assessments Over Time"
// replaces "Patient Admissions" (both trend lines; ours is real).
//
// HONEST ACCESS-CONTROL NOTE: unchanged from before -- this page (and
// its endpoints) rely on the frontend hiding the Admin nav link from
// non-admin users, not real server-side auth. See auth.py's docstring.

// Scoped dark-theme token overrides -- every child element below still
// references the SAME var(--color-surface) etc. tokens the rest of the
// app uses, so this single object is the only place the dark palette
// is defined. Tier accent colors (red/orange/yellow/green) are left
// alone -- they're already bright/saturated enough to read well on a
// dark background unchanged.
const DARK_THEME_VARS = {
  '--color-surface': '#1E293B',
  '--color-border': '#334155',
  '--color-ink': '#E2E8F0',
  '--color-ink-muted': '#94A3B8',
  '--color-teal-light': 'rgba(45, 212, 191, 0.16)',
  '--tier-orange-bg': 'rgba(234, 88, 12, 0.18)',
  '--tier-yellow-bg': 'rgba(202, 138, 4, 0.18)',
}

const TIER_COLORS = {
  Red: '#DC2626', Orange: '#EA580C', Yellow: '#CA8A04', Green: '#16A34A', Blue: '#2563EB',
}
const DONUT_COLORS = ['#2DD4BF', '#EA580C', '#CA8A04', '#16A34A', '#2563EB', '#DC2626']

export default function AdminPage() {
  const [users, setUsers] = useState(null)
  const [stats, setStats] = useState(null)
  const [pending, setPending] = useState(null)
  const [doctors, setDoctors] = useState(null)
  const [error, setError] = useState(null)
  const [actionError, setActionError] = useState(null)

  function loadAll() {
    getAllUsers().then((d) => setUsers(d.users)).catch((err) => setError(err.message))
    getAdminDashboardStats().then(setStats).catch((err) => setError(err.message))
    getPendingReviews().then((d) => setPending(d.pending)).catch((err) => setError(err.message))
    getAvailableDoctors().then((d) => setDoctors(d.doctors)).catch((err) => setError(err.message))
  }

  useEffect(loadAll, [])

  const roleCounts = (users || []).reduce((acc, u) => {
    acc[u.role] = (acc[u.role] || 0) + 1
    return acc
  }, {})

  return (
    <div style={{ ...DARK_THEME_VARS, background: '#141B29', color: 'var(--color-ink)', margin: 'calc(-1 * var(--space-8))', padding: 'var(--space-8)', minHeight: '100%' }}>
    <div style={{ maxWidth: 1000 }}>
      <h1 style={{ fontSize: 24, marginBottom: 4 }}>Admin Dashboard</h1>
      <p style={{ color: 'var(--color-ink-muted)', fontSize: 14, marginTop: 0, marginBottom: 'var(--space-6)' }}>
        Real system data: patients, assessments, reviews, and registered users.
      </p>

      {error && (
        <div style={{ fontSize: 13, color: 'var(--tier-red)', marginBottom: 'var(--space-4)' }}>
          Some data could not load ({error}).
        </div>
      )}

      {/* Stat cards */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 'var(--space-6)', flexWrap: 'wrap' }}>
        <StatCard label="Total Patients" value={stats?.total_patients ?? '—'} />
        <StatCard label="Pending Review" value={stats?.pending_count ?? '—'} accent="var(--tier-yellow)" />
        <StatCard label="Available Doctors" value={stats?.available_doctors_count ?? '—'} accent="var(--tier-green)" />
        <StatCard label="Total Assessments" value={stats?.total_assessments ?? '—'} />
      </div>

      {/* Charts row -- auto-fit collapses to a single column on narrow
          screens instead of squeezing two charts side by side */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 12, marginBottom: 'var(--space-6)' }}>
        <ChartCard title="Assessments Over Time (7 days)">
          {stats && stats.assessments_by_day.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={stats.assessments_by_day}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2D3B52" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#94A3B8' }} />
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', color: '#E2E8F0' }} />
                <Line type="monotone" dataKey="count" stroke="#2DD4BF" strokeWidth={2} dot={{ r: 3, fill: '#2DD4BF' }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart text="No assessments in the last 7 days yet." />
          )}
        </ChartCard>

        <ChartCard title="Diagnosis Breakdown">
          {stats && stats.diagnosis_breakdown.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={stats.diagnosis_breakdown} dataKey="count" nameKey="disease"
                  cx="50%" cy="50%" innerRadius={40} outerRadius={70}
                >
                  {stats.diagnosis_breakdown.map((_, i) => (
                    <Cell key={i} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#1E293B', border: '1px solid #334155', color: '#E2E8F0' }} />
                <Legend wrapperStyle={{ fontSize: 11, color: '#94A3B8' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChart text="No diagnoses recorded yet." />
          )}
        </ChartCard>
      </div>

      {/* Quick links + Recent activity */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12, marginBottom: 'var(--space-8)' }}>
        <ChartCard title="Quick Links">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <Link to="/intake" style={quickLinkStyle}>+ New Assessment</Link>
            <a href="#pending-review" style={quickLinkStyle}>
              Review Pending {stats?.pending_count ? `(${stats.pending_count})` : ''}
            </a>
          </div>
        </ChartCard>

        <ChartCard title="Recent Activity">
          {stats && stats.recent_activity.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, maxHeight: 200, overflowY: 'auto' }}>
              {stats.recent_activity.map((a, i) => (
                <div key={i} style={{ fontSize: 12.5 }}>
                  <span>{a.text}</span>
                  <div style={{ fontSize: 11, color: 'var(--color-ink-muted)' }}>
                    {new Date(a.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyChart text="No activity yet." />
          )}
        </ChartCard>
      </div>

      {/* Pending review queue */}
      <h2 id="pending-review" style={{ fontSize: 18, marginBottom: 'var(--space-4)' }}>Pending Review</h2>
      {actionError && <div style={{ fontSize: 13, color: 'var(--tier-red)', marginBottom: 'var(--space-4)' }}>{actionError}</div>}
      {pending && pending.length === 0 && (
        <div style={{ fontSize: 13, color: 'var(--color-ink-muted)', marginBottom: 'var(--space-8)' }}>
          Nothing awaiting review right now.
        </div>
      )}
      {pending && pending.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 'var(--space-8)' }}>
          {pending.map((p) => (
            <PendingCard
              key={p.decision_id}
              decision={p}
              doctors={doctors || []}
              onDone={() => { setActionError(null); loadAll() }}
              onError={setActionError}
            />
          ))}
        </div>
      )}

      {/* Registered users table */}
      <h2 style={{ fontSize: 18, marginBottom: 'var(--space-4)' }}>Registered Users</h2>
      {users && (
        <>
          <div style={{ display: 'flex', gap: 12, marginBottom: 'var(--space-6)', flexWrap: 'wrap' }}>
            <StatCard label="Total Users" value={users.length} small />
            <StatCard label="Clinicians" value={roleCounts.clinician || 0} small />
            <StatCard label="Doctors" value={roleCounts.doctor || 0} small />
            <StatCard label="Patients" value={roleCounts.patient || 0} small />
            <StatCard label="Admins" value={roleCounts.admin || 0} small />
          </div>

          <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#F7F9FA', textAlign: 'left' }}>
                    <th style={thStyle}>Username</th><th style={thStyle}>Role</th><th style={thStyle}>Registered</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u, i) => (
                    <tr key={i} style={{ borderTop: '1px solid var(--color-border)' }}>
                      <td style={tdStyle}>{u.username}</td>
                      <td style={tdStyle}>
                        <span style={{
                          fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 999,
                          background: u.role === 'admin' ? 'var(--tier-orange-bg)' : 'var(--color-teal-light)',
                          color: u.role === 'admin' ? 'var(--tier-orange)' : 'var(--color-teal)',
                        }}>
                          {u.role}
                        </span>
                      </td>
                      <td style={tdStyle}>{new Date(u.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
    </div>
  )
}

function PendingCard({ decision: d, doctors, onDone, onError }) {
  const [open, setOpen] = useState(false)
  const [showDoctorPicker, setShowDoctorPicker] = useState(false)
  const [selectedDoctor, setSelectedDoctor] = useState('')
  const [busy, setBusy] = useState(false)
  const tierColor = TIER_COLORS[d.tier] || 'var(--color-ink)'

  async function handleApprove() {
    if (!selectedDoctor) { onError('Pick a doctor to assign this case to first.'); return }
    setBusy(true)
    try {
      const adminUserId = localStorage.getItem('hans_triage_user_id')
      await approveDecision(d.decision_id, parseInt(selectedDoctor, 10), adminUserId)
      onDone()
    } catch (err) {
      onError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleReject() {
    setBusy(true)
    try {
      const adminUserId = localStorage.getItem('hans_triage_user_id')
      await rejectDecision(d.decision_id, adminUserId, 'Rejected by admin')
      onDone()
    } catch (err) {
      onError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div style={{ background: 'var(--color-surface)', border: `1px solid var(--tier-yellow)`, borderRadius: 'var(--radius)', overflow: 'hidden' }}>
      <div
        style={{ padding: 'var(--space-5)', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}
        onClick={() => setOpen((v) => !v)}
      >
        <div>
          <div style={{ fontSize: 13, color: 'var(--color-ink-muted)', marginBottom: 4 }}>
            {new Date(d.created_at).toLocaleString()} · <span style={{ fontFamily: 'var(--font-mono)' }}>{d.pseudonym}</span> · {d.age_years}y
          </div>
          <div style={{ fontSize: 15, fontWeight: 600 }}>
            {d.top_diagnosis || 'Assessment recorded'}{' '}
            <span style={{ color: tierColor, fontWeight: 700 }}>· {d.tier}</span>
          </div>
        </div>
        <span style={{ fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 999, background: 'var(--tier-yellow-bg)', color: 'var(--tier-yellow)' }}>
          Pending Review
        </span>
      </div>

      {open && (
        <div style={{ padding: '0 var(--space-5) var(--space-5)', borderTop: '1px solid var(--color-border)' }}>
          <div style={{ marginTop: 'var(--space-4)', marginBottom: 'var(--space-4)' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-ink-muted)', marginBottom: 4 }}>SYMPTOMS</div>
            <div style={{ fontSize: 13, marginBottom: 10 }}>{(d.symptoms || []).join(', ') || '—'}</div>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-ink-muted)', marginBottom: 4 }}>RATIONALE</div>
            <div style={{ fontSize: 13 }}>{d.rationale || '—'}</div>
          </div>

          {!showDoctorPicker ? (
            <div style={{ display: 'flex', gap: 10 }}>
              <button onClick={(e) => { e.stopPropagation(); setShowDoctorPicker(true) }} style={approveButtonStyle}>
                Approve…
              </button>
              <button onClick={(e) => { e.stopPropagation(); handleReject() }} disabled={busy} style={rejectButtonStyle}>
                Reject
              </button>
            </div>
          ) : (
            <div onClick={(e) => e.stopPropagation()}>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-ink-muted)', marginBottom: 6 }}>
                ASSIGN TO AN AVAILABLE DOCTOR
              </div>
              {doctors.length === 0 ? (
                <div style={{ fontSize: 13, color: 'var(--tier-red)', marginBottom: 10 }}>
                  No doctors are currently marked available.
                </div>
              ) : (
                <select
                  value={selectedDoctor}
                  onChange={(e) => setSelectedDoctor(e.target.value)}
                  style={{ padding: '8px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--color-border)', fontSize: 13, marginBottom: 10, width: '100%' }}
                >
                  <option value="">Select a doctor…</option>
                  {doctors.map((doc) => (
                    <option key={doc.user_id} value={doc.user_id}>{doc.username}</option>
                  ))}
                </select>
              )}
              <div style={{ display: 'flex', gap: 10 }}>
                <button onClick={handleApprove} disabled={busy || doctors.length === 0} style={approveButtonStyle}>
                  {busy ? 'Assigning…' : 'Confirm Approve & Assign'}
                </button>
                <button onClick={() => setShowDoctorPicker(false)} style={rejectButtonStyle}>Cancel</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, accent, small }) {
  return (
    <div style={{ flex: 1, background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', padding: small ? 'var(--space-3)' : 'var(--space-4)' }}>
      <div style={{ fontSize: small ? 18 : 24, fontWeight: 700, color: accent || 'var(--color-teal)', fontFamily: 'var(--font-mono)' }}>{value}</div>
      <div style={{ fontSize: 12, color: 'var(--color-ink-muted)' }}>{label}</div>
    </div>
  )
}

function ChartCard({ title, children }) {
  return (
    <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', padding: 'var(--space-5)' }}>
      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 'var(--space-3)' }}>{title}</div>
      {children}
    </div>
  )
}

function EmptyChart({ text }) {
  return (
    <div style={{ height: 200, display: 'grid', placeItems: 'center', color: 'var(--color-ink-muted)', fontSize: 13 }}>
      {text}
    </div>
  )
}

const quickLinkStyle = {
  display: 'block', textDecoration: 'none', color: 'var(--color-teal)', fontWeight: 600, fontSize: 13,
  background: 'var(--color-teal-light)', padding: '10px 14px', borderRadius: 'var(--radius-sm)',
}

const approveButtonStyle = {
  background: 'var(--tier-green)', color: 'white', border: 'none',
  borderRadius: 999, padding: '9px 20px', fontWeight: 600, fontSize: 13, cursor: 'pointer',
}
const rejectButtonStyle = {
  background: 'none', color: 'var(--tier-red)', border: '1px solid var(--tier-red)',
  borderRadius: 999, padding: '9px 20px', fontWeight: 600, fontSize: 13, cursor: 'pointer',
}

const thStyle = { padding: '10px 16px', fontWeight: 600, color: 'var(--color-ink-muted)' }
const tdStyle = { padding: '10px 16px' }
