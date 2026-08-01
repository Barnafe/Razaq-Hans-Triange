import React, { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { getPatientHistory } from '../api/client'
import IntakePage from './IntakePage'

// Restructured per request: one page, three tabs (Profile / New
// Assessment / History) instead of a separate dashboard with its own
// nav item. "New Assessment" reuses the existing IntakePage component
// directly (it's already role-aware -- submits as a patient
// self-submission when the logged-in role is 'patient') rather than
// duplicating the whole multi-step form.

const STATUS_META = {
  pending_review: { label: 'Pending Review', color: 'var(--tier-yellow)', bg: 'var(--tier-yellow-bg)' },
  approved: { label: 'Approved', color: 'var(--tier-green)', bg: 'var(--tier-green-bg)' },
  rejected: { label: 'Rejected', color: 'var(--tier-red)', bg: 'var(--tier-red-bg)' },
  attended: { label: 'Attended', color: 'var(--color-teal)', bg: 'var(--color-teal-light)' },
  finalized: { label: 'Finalized', color: 'var(--color-ink-muted)', bg: '#F0F2F4' },
}

const TABS = ['Profile', 'New Assessment', 'History']

export default function PatientDashboardPage() {
  const location = useLocation()
  const [tab, setTab] = useState(location.state?.initialTab || 'Profile')

  return (
    <div style={{ maxWidth: 800 }}>
      <h1 style={{ fontSize: 24, marginBottom: 'var(--space-4)' }}>My Profile</h1>

      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid var(--color-border)', marginBottom: 'var(--space-6)' }}>
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              padding: '10px 16px', fontSize: 14, fontWeight: 600,
              color: tab === t ? 'var(--color-teal)' : 'var(--color-ink-muted)',
              borderBottom: tab === t ? '2px solid var(--color-teal)' : '2px solid transparent',
              marginBottom: -1,
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'Profile' && <ProfileTab />}
      {tab === 'New Assessment' && <IntakePage />}
      {tab === 'History' && <HistoryTab />}
    </div>
  )
}

function ProfileTab() {
  const username = localStorage.getItem('hans_triage_username')
  return (
    <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', padding: 'var(--space-6)', maxWidth: 420 }}>
      <ProfileRow label="Username" value={username || '—'} />
      <ProfileRow label="Role" value="Patient" />
    </div>
  )
}

function ProfileRow({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--color-border)' }}>
      <span style={{ fontSize: 13, color: 'var(--color-ink-muted)' }}>{label}</span>
      <span style={{ fontSize: 13, fontWeight: 600 }}>{value}</span>
    </div>
  )
}

function HistoryTab() {
  const [history, setHistory] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    const userId = localStorage.getItem('hans_triage_user_id')
    getPatientHistory(userId)
      .then((data) => setHistory(data.history))
      .catch((err) => setError(err.message))
  }, [])

  if (error) return <div style={{ fontSize: 13, color: 'var(--tier-red)' }}>Could not load your history ({error}).</div>
  if (history === null) return <div style={{ fontSize: 14, color: 'var(--color-ink-muted)' }}>Loading…</div>

  if (history.length === 0) {
    return (
      <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', padding: 'var(--space-8)', textAlign: 'center', color: 'var(--color-ink-muted)', fontSize: 14 }}>
        You haven't submitted an assessment yet. Use the "New Assessment" tab to get started.
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {history.map((h) => {
        const meta = STATUS_META[h.status] || STATUS_META.finalized
        return (
          <div key={h.decision_id} style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', padding: 'var(--space-5)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <div style={{ fontSize: 13, color: 'var(--color-ink-muted)', marginBottom: 4 }}>
                  {new Date(h.created_at).toLocaleString()}
                </div>
                <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>
                  {h.top_diagnosis || 'Assessment recorded'}
                </div>
                <div style={{ fontSize: 13, color: 'var(--color-ink-muted)' }}>
                  Symptoms: {(h.symptoms || []).join(', ') || '—'}
                </div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                <span style={{ fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 999, background: meta.bg, color: meta.color }}>
                  {meta.label}
                </span>
                <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--tier-orange)' }}>Tier: {h.tier}</span>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
