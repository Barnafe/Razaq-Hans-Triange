import React, { useEffect, useState } from 'react'
import { getRecentEncounters } from '../api/client'

// Real dashboard -- fetches actual persisted triage decisions from
// PostgreSQL (backend/app/db/persistence.py). Deliberately does NOT show
// fake stats (revenue, staff counts, etc. from the supervisor's generic
// hospital-admin reference) since we have no real data source for those
// -- only what our system actually tracks: triage decisions.

const TIER_COLORS = {
  Blue: 'var(--tier-blue)', Green: 'var(--tier-green)', Yellow: 'var(--tier-yellow)',
  Orange: 'var(--tier-orange)', Red: 'var(--tier-red)',
}
const TIER_BG = {
  Blue: 'var(--tier-blue-bg)', Green: 'var(--tier-green-bg)', Yellow: 'var(--tier-yellow-bg)',
  Orange: 'var(--tier-orange-bg)', Red: 'var(--tier-red-bg)',
}

export default function DashboardPage() {
  const [encounters, setEncounters] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getRecentEncounters(20)
      .then((data) => setEncounters(data.encounters))
      .catch((err) => setError(err.message))
  }, [])

  const tierCounts = (encounters || []).reduce((acc, e) => {
    acc[e.tier] = (acc[e.tier] || 0) + 1
    return acc
  }, {})

  // Additional real, honest aggregate stats -- added after feedback asking
  // for admin-relevant data. Deliberately NOT showing fake hospital-ops
  // metrics (revenue, staff counts, billing) since we have no real source
  // for those -- everything below is computed from actual persisted data.
  const uniquePatients = new Set((encounters || []).map((e) => e.pseudonym)).size
  const avgAge = encounters && encounters.length
    ? (encounters.reduce((sum, e) => sum + e.age_years, 0) / encounters.length).toFixed(1)
    : '—'
  const diagnosisCounts = (encounters || []).reduce((acc, e) => {
    if (e.top_diagnosis) acc[e.top_diagnosis] = (acc[e.top_diagnosis] || 0) + 1
    return acc
  }, {})
  const topDiagnosis = Object.entries(diagnosisCounts).sort((a, b) => b[1] - a[1])[0]

  return (
    <div style={{ maxWidth: 900 }}>
      <h1 style={{ fontSize: 24, marginBottom: 4 }}>Dashboard</h1>
      <p style={{ color: 'var(--color-ink-muted)', fontSize: 14, marginTop: 0, marginBottom: 'var(--space-8)' }}>
        Recent triage assessments recorded by this system.
      </p>

      {error && (
        <div
          style={{
            background: 'var(--tier-yellow-bg)', border: '1px solid var(--tier-yellow)',
            borderRadius: 'var(--radius-sm)', padding: 'var(--space-4)', fontSize: 13,
            color: '#7C5E00', marginBottom: 'var(--space-6)',
          }}
        >
          Could not load recent assessments ({error}). The database may not be
          running or reachable -- this page requires PostgreSQL to be set up
          per docs/SETUP.md.
        </div>
      )}

      {!error && encounters === null && (
        <div style={{ fontSize: 14, color: 'var(--color-ink-muted)' }}>Loading…</div>
      )}

      {encounters && (
        <>
          <div style={{ display: 'flex', gap: 12, marginBottom: 'var(--space-6)', flexWrap: 'wrap' }}>
            <SummaryCard label="Total Assessments" value={encounters.length} />
            <SummaryCard label="Unique Patients" value={uniquePatients} />
            <SummaryCard label="Average Age" value={avgAge} />
            <SummaryCard label="Most Common Diagnosis" value={topDiagnosis ? topDiagnosis[0] : '—'} small />
          </div>

          <div style={{ display: 'flex', gap: 12, marginBottom: 'var(--space-8)', flexWrap: 'wrap' }}>
            {['Red', 'Orange', 'Yellow', 'Green', 'Blue'].map((tier) => (
              <div
                key={tier}
                style={{
                  background: TIER_BG[tier], border: `1px solid ${TIER_COLORS[tier]}`,
                  borderRadius: 'var(--radius)', padding: 'var(--space-4)', minWidth: 100, textAlign: 'center',
                }}
              >
                <div style={{ fontSize: 22, fontWeight: 700, color: TIER_COLORS[tier], fontFamily: 'var(--font-mono)' }}>
                  {tierCounts[tier] || 0}
                </div>
                <div style={{ fontSize: 12, color: 'var(--color-ink-muted)' }}>{tier}</div>
              </div>
            ))}
          </div>

          {encounters.length === 0 ? (
            <div style={{ fontSize: 14, color: 'var(--color-ink-muted)' }}>
              No assessments recorded yet. Run one from "New Assessment" to see it here.
            </div>
          ) : (
            <div style={{ background: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)', overflow: 'hidden' }}>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ background: '#F7F9FA', textAlign: 'left' }}>
                      <Th></Th><Th>Patient</Th><Th>Age</Th><Th>Tier</Th><Th>Top Diagnosis</Th><Th>When</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {encounters.map((e) => (
                      <ExpandableRow key={e.decision_id} encounter={e} tierColor={TIER_COLORS[e.tier]} />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function ExpandableRow({ encounter: e, tierColor }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <tr
        style={{ borderTop: '1px solid var(--color-border)', cursor: 'pointer' }}
        onClick={() => setOpen((v) => !v)}
      >
        <Td>
          <span style={{ display: 'inline-block', transform: open ? 'rotate(90deg)' : 'none', transition: 'transform 0.15s', color: 'var(--color-ink-muted)' }}>
            ▸
          </span>
        </Td>
        <Td mono>{e.pseudonym}</Td>
        <Td>{e.age_years}</Td>
        <Td>
          <span style={{ color: tierColor, fontWeight: 600 }}>{e.tier}</span>
        </Td>
        <Td>{e.top_diagnosis || '—'}</Td>
        <Td>{new Date(e.created_at).toLocaleString()}</Td>
      </tr>
      {open && (
        <tr style={{ borderTop: '1px solid var(--color-border)' }}>
          <td colSpan={6} style={{ padding: 'var(--space-4) 16px 16px 44px', background: '#FAFBFC' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-ink-muted)', marginBottom: 4 }}>
                  DIFFERENTIAL DIAGNOSIS
                </div>
                {(e.differential_diagnosis || []).length === 0 ? (
                  <div style={{ fontSize: 13, color: 'var(--color-ink-muted)' }}>—</div>
                ) : (
                  <ol style={{ margin: 0, paddingLeft: 18, fontSize: 13 }}>
                    {e.differential_diagnosis.map((d, i) => (
                      <li key={i}>
                        {d.disease}
                        {typeof d.probability === 'number' ? ` — ${(d.probability * 100).toFixed(0)}%` : ''}
                      </li>
                    ))}
                  </ol>
                )}

                {e.red_flag_alerts && e.red_flag_alerts.length > 0 && (
                  <>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--tier-red)', marginTop: 10, marginBottom: 4 }}>
                      RED FLAGS
                    </div>
                    <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: 'var(--tier-red)' }}>
                      {e.red_flag_alerts.map((f, i) => (
                        <li key={i}>{typeof f === 'string' ? f : JSON.stringify(f)}</li>
                      ))}
                    </ul>
                  </>
                )}
              </div>

              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-ink-muted)', marginBottom: 4 }}>
                  VITALS
                </div>
                <div style={{ fontSize: 13, color: 'var(--color-ink)', lineHeight: 1.7 }}>
                  {e.vitals?.temperature != null && <div>Temp: {e.vitals.temperature}°C</div>}
                  {e.vitals?.heart_rate != null && <div>HR: {e.vitals.heart_rate} bpm</div>}
                  {e.vitals?.respiratory_rate != null && <div>RR: {e.vitals.respiratory_rate} /min</div>}
                  {(e.vitals?.systolic != null || e.vitals?.diastolic != null) && (
                    <div>BP: {e.vitals.systolic ?? '—'}/{e.vitals.diastolic ?? '—'}</div>
                  )}
                  {e.vitals?.spo2 != null && <div>SpO2: {e.vitals.spo2}%</div>}
                </div>

                <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-ink-muted)', marginTop: 10, marginBottom: 4 }}>
                  SYMPTOMS
                </div>
                <div style={{ fontSize: 13 }}>{(e.symptoms || []).join(', ') || '—'}</div>
              </div>
            </div>

            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-ink-muted)', marginTop: 10, marginBottom: 4 }}>
              RATIONALE
            </div>
            <div style={{ fontSize: 13, color: 'var(--color-ink)' }}>{e.rationale || '—'}</div>
          </td>
        </tr>
      )}
    </>
  )
}

function SummaryCard({ label, value, small }) {
  return (
    <div
      style={{
        background: 'var(--color-surface)', border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius)', padding: 'var(--space-4)', minWidth: 140, flex: small ? 2 : 1,
      }}
    >
      <div style={{ fontSize: small ? 15 : 22, fontWeight: 700, color: 'var(--color-teal)', fontFamily: small ? 'var(--font-body)' : 'var(--font-mono)' }}>
        {value}
      </div>
      <div style={{ fontSize: 12, color: 'var(--color-ink-muted)' }}>{label}</div>
    </div>
  )
}

function Th({ children }) {
  return <th style={{ padding: '10px 16px', fontWeight: 600, color: 'var(--color-ink-muted)' }}>{children}</th>
}
function Td({ children, mono }) {
  return <td style={{ padding: '10px 16px', fontFamily: mono ? 'var(--font-mono)' : undefined }}>{children}</td>
}
