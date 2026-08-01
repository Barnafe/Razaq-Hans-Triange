import React, { useEffect, useState } from 'react'
import { getAssignedDecisions, markAttended } from '../api/client'

const TIER_COLORS = {
  Blue: 'var(--tier-blue)', Green: 'var(--tier-green)', Yellow: 'var(--tier-yellow)',
  Orange: 'var(--tier-orange)', Red: 'var(--tier-red)',
}
const STATUS_META = {
  approved: { label: 'Awaiting You', color: 'var(--tier-orange)', bg: 'var(--tier-orange-bg)' },
  attended: { label: 'Attended', color: 'var(--tier-green)', bg: 'var(--tier-green-bg)' },
}

export default function DoctorDashboardPage() {
  const [assigned, setAssigned] = useState(null)
  const [error, setError] = useState(null)
  const [actionError, setActionError] = useState(null)

  function load() {
    const doctorId = localStorage.getItem('hans_triage_user_id')
    getAssignedDecisions(doctorId)
      .then((data) => setAssigned(data.assigned))
      .catch((err) => setError(err.message))
  }

  useEffect(load, [])

  async function handleAttend(decisionId) {
    setActionError(null)
    try {
      const doctorId = localStorage.getItem('hans_triage_user_id')
      await markAttended(decisionId, doctorId)
      load()
    } catch (err) {
      setActionError(err.message)
    }
  }

  const pendingCount = (assigned || []).filter((a) => a.status === 'approved').length

  return (
    <div style={{ maxWidth: 800 }}>
      <h1 style={{ fontSize: 24, marginBottom: 4 }}>My Patients</h1>
      <p style={{ color: 'var(--color-ink-muted)', fontSize: 14, marginTop: 0, marginBottom: 'var(--space-6)' }}>
        Cases an admin has assigned to you. {pendingCount > 0 && `${pendingCount} awaiting your attention.`}
      </p>

      {error && <div style={{ fontSize: 13, color: 'var(--tier-red)' }}>Could not load your patients ({error}).</div>}
      {actionError && <div style={{ fontSize: 13, color: 'var(--tier-red)', marginBottom: 'var(--space-4)' }}>{actionError}</div>}
      {!error && assigned === null && <div style={{ fontSize: 14, color: 'var(--color-ink-muted)' }}>Loading…</div>}

      {assigned && assigned.length === 0 && (
        <div
          style={{
            background: 'var(--color-surface)', border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius)', padding: 'var(--space-8)', textAlign: 'center',
            color: 'var(--color-ink-muted)', fontSize: 14,
          }}
        >
          No patients assigned to you yet.
        </div>
      )}

      {assigned && assigned.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {assigned.map((a) => (
            <PatientCard key={a.decision_id} decision={a} onAttend={() => handleAttend(a.decision_id)} />
          ))}
        </div>
      )}
    </div>
  )
}

function PatientCard({ decision: d, onAttend }) {
  const [open, setOpen] = useState(false)
  const statusMeta = STATUS_META[d.status] || STATUS_META.approved
  const tierColor = TIER_COLORS[d.tier] || 'var(--color-ink)'

  return (
    <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
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
        <span
          style={{
            fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 999,
            background: statusMeta.bg, color: statusMeta.color, whiteSpace: 'nowrap',
          }}
        >
          {statusMeta.label}
        </span>
      </div>

      {open && (
        <div style={{ padding: '0 var(--space-5) var(--space-5)', borderTop: '1px solid var(--color-border)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 'var(--space-4)' }}>
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-ink-muted)', marginBottom: 4 }}>DIFFERENTIAL DIAGNOSIS</div>
              {(d.differential_diagnosis || []).length === 0 ? (
                <div style={{ fontSize: 13, color: 'var(--color-ink-muted)' }}>—</div>
              ) : (
                <ol style={{ margin: 0, paddingLeft: 18, fontSize: 13 }}>
                  {d.differential_diagnosis.map((diag, i) => (
                    <li key={i}>
                      {diag.disease}
                      {typeof diag.probability === 'number' ? ` — ${(diag.probability * 100).toFixed(0)}%` : ''}
                    </li>
                  ))}
                </ol>
              )}
              {d.red_flag_alerts && d.red_flag_alerts.length > 0 && (
                <>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--tier-red)', marginTop: 10, marginBottom: 4 }}>RED FLAGS</div>
                  <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: 'var(--tier-red)' }}>
                    {d.red_flag_alerts.map((f, i) => <li key={i}>{typeof f === 'string' ? f : JSON.stringify(f)}</li>)}
                  </ul>
                </>
              )}
            </div>
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-ink-muted)', marginBottom: 4 }}>SYMPTOMS</div>
              <div style={{ fontSize: 13, marginBottom: 10 }}>{(d.symptoms || []).join(', ') || '—'}</div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-ink-muted)', marginBottom: 4 }}>RATIONALE</div>
              <div style={{ fontSize: 13 }}>{d.rationale || '—'}</div>
            </div>
          </div>

          {d.status === 'approved' && (
            <button onClick={(e) => { e.stopPropagation(); onAttend() }} style={attendButtonStyle}>
              Mark Attended
            </button>
          )}
        </div>
      )}
    </div>
  )
}

const attendButtonStyle = {
  marginTop: 'var(--space-4)', background: 'var(--color-teal)', color: 'white',
  border: 'none', borderRadius: 999, padding: '10px 24px', fontWeight: 600, fontSize: 13, cursor: 'pointer',
}
