import React, { useEffect, useState } from 'react'
import { getAssignedDecisions, markAttended } from '../api/client'

// Renamed from "Doctor Dashboard" to "Clinical" per request: simplified
// to a Profile section + patient list, no stats/charts (it never had
// those -- this was always a plain list, unlike Admin).
//
// SCOPE NOTE, not silently decided: the request was "profile + history
// of patients they have attended to, that's all." Taken literally, that
// would remove the "Mark Attended" action entirely -- but that action
// IS the only way a case ever reaches "attended" in the first place, so
// removing it would break the approve -> attend loop this whole feature
// was built for. Kept it, under a small "Awaiting You" section above
// the history, rather than silently dropping a piece of the workflow.
// Flagging this so it can be corrected if the list should really be
// read-only and attending should happen somewhere else.

const TIER_COLORS = {
  Blue: 'var(--tier-blue)', Green: 'var(--tier-green)', Yellow: 'var(--tier-yellow)',
  Orange: 'var(--tier-orange)', Red: 'var(--tier-red)',
}

export default function ClinicalPage() {
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

  const awaitingYou = (assigned || []).filter((a) => a.status === 'approved')
  const attendedHistory = (assigned || []).filter((a) => a.status === 'attended')

  return (
    <div style={{ maxWidth: 800 }}>
      <h1 style={{ fontSize: 24, marginBottom: 'var(--space-6)' }}>Clinical</h1>

      {/* Profile */}
      <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', padding: 'var(--space-6)', maxWidth: 420, marginBottom: 'var(--space-8)' }}>
        <ProfileRow label="Username" value={localStorage.getItem('hans_triage_username') || '—'} />
        <ProfileRow label="Role" value="Doctor" />
      </div>

      {error && <div style={{ fontSize: 13, color: 'var(--tier-red)' }}>Could not load your patients ({error}).</div>}
      {actionError && <div style={{ fontSize: 13, color: 'var(--tier-red)', marginBottom: 'var(--space-4)' }}>{actionError}</div>}
      {!error && assigned === null && <div style={{ fontSize: 14, color: 'var(--color-ink-muted)' }}>Loading…</div>}

      {assigned && awaitingYou.length > 0 && (
        <>
          <h2 style={{ fontSize: 16, marginBottom: 'var(--space-4)' }}>Awaiting You</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 'var(--space-8)' }}>
            {awaitingYou.map((a) => (
              <PatientCard key={a.decision_id} decision={a} onAttend={() => handleAttend(a.decision_id)} />
            ))}
          </div>
        </>
      )}

      <h2 style={{ fontSize: 16, marginBottom: 'var(--space-4)' }}>Patients I've Attended</h2>
      {assigned && attendedHistory.length === 0 && (
        <div style={{ fontSize: 13, color: 'var(--color-ink-muted)' }}>No attended patients yet.</div>
      )}
      {assigned && attendedHistory.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {attendedHistory.map((a) => <PatientCard key={a.decision_id} decision={a} />)}
        </div>
      )}
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

function PatientCard({ decision: d, onAttend }) {
  const [open, setOpen] = useState(false)
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
      </div>

      {open && (
        <div style={{ padding: '0 var(--space-5) var(--space-5)', borderTop: '1px solid var(--color-border)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginTop: 'var(--space-4)' }}>
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

          {d.status === 'approved' && onAttend && (
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
