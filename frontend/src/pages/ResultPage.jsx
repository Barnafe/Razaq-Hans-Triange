import React from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import StepProgress from '../components/StepProgress'

const TIER_ORDER = ['Blue', 'Green', 'Yellow', 'Orange', 'Red']
const TIER_COLORS = {
  Blue: 'var(--tier-blue)', Green: 'var(--tier-green)', Yellow: 'var(--tier-yellow)',
  Orange: 'var(--tier-orange)', Red: 'var(--tier-red)',
}
const TIER_BG = {
  Blue: 'var(--tier-blue-bg)', Green: 'var(--tier-green-bg)', Yellow: 'var(--tier-yellow-bg)',
  Orange: 'var(--tier-orange-bg)', Red: 'var(--tier-red-bg)',
}
// Same step list IntakePage uses, plus the final "Result" step -- matches
// the supervisor's diagnosis-result reference (6-step progress bar ending
// in "Assessment Result"), continuing the same stepper across both pages
// instead of a disconnected one.
const RESULT_STEPS = ['Personal Data', 'Vitals', 'Symptoms', 'Image', 'Review', 'Result']

export default function ResultPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const result = location.state?.result
  const submittedSymptoms = location.state?.submittedSymptoms || []
  const isPatientSelfSubmit = location.state?.isPatientSelfSubmit || false

  if (!result) {
    return (
      <div>
        <p>No assessment result to show yet.</p>
        <button onClick={() => navigate('/intake')} style={linkButtonStyle}>Start a new assessment</button>
      </div>
    )
  }

  const { triage, partial_failures } = result

  // triage can be null even on a 200 response: the backend isolates each
  // agent's failure so one broken agent doesn't take down the whole
  // request, but that means the core triage_agent itself can fail and
  // still return normally with triage: null + a reason in partial_failures.
  // Surface that clearly instead of crashing on triage.whatever below.
  if (!triage) {
    return (
      <div style={{ maxWidth: 760 }}>
        <StepProgress steps={RESULT_STEPS} currentIndex={RESULT_STEPS.length - 1} />
        <h1 style={{ fontSize: 24, marginBottom: 'var(--space-6)' }}>Assessment Result</h1>
        <div
          style={{
            background: 'var(--tier-red-bg)', border: '1px solid var(--tier-red)',
            borderRadius: 'var(--radius)', padding: 'var(--space-6)', marginBottom: 'var(--space-6)',
          }}
        >
          <h2 style={{ fontSize: 18, color: 'var(--tier-red)', marginBottom: 8 }}>
            The triage engine couldn't produce a result for this submission
          </h2>
          <p style={{ fontSize: 14, color: 'var(--color-ink)', marginBottom: 4 }}>
            This is a backend calculation error, not a lost submission -- nothing was
            corrupted, but no tier could be computed for the values you entered.
          </p>
          {partial_failures?.triage_agent && (
            <pre style={{
              fontSize: 12, background: 'var(--color-surface)', padding: 10, borderRadius: 6,
              marginTop: 10, whiteSpace: 'pre-wrap', color: 'var(--color-ink-muted)',
            }}>{partial_failures.triage_agent}</pre>
          )}
        </div>
        <button onClick={() => navigate('/intake')} style={linkButtonStyle}>Start a new assessment</button>
      </div>
    )
  }

  const tier = triage?.urgency_classification?.tier
  const topMatch = triage.differential_diagnosis?.[0]

  return (
    <div style={{ maxWidth: 760 }}>
      <StepProgress steps={RESULT_STEPS} currentIndex={RESULT_STEPS.length - 1} />

      <h1 style={{ fontSize: 24, marginBottom: 'var(--space-6)' }}>Assessment Result</h1>

      {isPatientSelfSubmit && (
        <div
          style={{
            background: 'var(--color-teal-light)', border: '1px solid var(--color-teal)',
            borderRadius: 'var(--radius-sm)', padding: 'var(--space-3) var(--space-4)',
            fontSize: 13, marginBottom: 'var(--space-6)', color: 'var(--color-teal-dark)',
          }}
        >
          This has been submitted to an admin for review. You'll be able to see its status
          (and which doctor it's assigned to, once approved) on your{' '}
          <Link to="/dashboard/patient" state={{ initialTab: 'History' }} style={{ color: 'inherit', fontWeight: 600 }}>My Profile</Link> page.
        </div>
      )}

      {partial_failures && (
        <div
          style={{
            background: '#FFF7ED', border: '1px solid var(--tier-orange)',
            borderRadius: 'var(--radius-sm)', padding: 'var(--space-3) var(--space-4)',
            fontSize: 13, marginBottom: 'var(--space-6)', color: 'var(--tier-orange)',
          }}
        >
          Note: some non-critical system checks did not complete ({Object.keys(partial_failures).join(', ')}),
          but this did not affect the triage decision below.
        </div>
      )}

      {/* Signature element: the real 5-level urgency spectrum, showing
          exactly where this patient's result sits along it. */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <div style={{ display: 'flex', borderRadius: 999, overflow: 'hidden', height: 10 }}>
          {TIER_ORDER.map((t) => (
            <div key={t} style={{ flex: 1, background: TIER_COLORS[t], opacity: t === tier ? 1 : 0.25 }} />
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--color-ink-muted)', marginTop: 4 }}>
          {TIER_ORDER.map((t) => <span key={t}>{t}</span>)}
        </div>
      </div>

      {/* Urgency card: description on the left, big tier badge on the
          right -- same two-column composition as the reference's
          Urgency Level card with its circular score. */}
      <div
        style={{
          background: TIER_BG[tier], border: `1px solid ${TIER_COLORS[tier]}`,
          borderRadius: 'var(--radius)', padding: 'var(--space-6)', marginBottom: 'var(--space-6)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-6)',
        }}
      >
        <div>
          <h2 style={{ fontSize: 22, color: TIER_COLORS[tier], marginBottom: 6 }}>
            Urgency Level: {tier}
          </h2>
          <div style={{ fontSize: 13, color: 'var(--color-ink-muted)', marginBottom: 8 }}>
            {triage.urgency_classification.label} · max wait {triage.urgency_classification.max_recommended_wait}
          </div>
          <p style={{ fontSize: 14, lineHeight: 1.6, color: 'var(--color-ink)', margin: 0 }}>
            {triage.urgency_classification.rationale}
          </p>
        </div>
        <div
          style={{
            width: 84, height: 84, borderRadius: '50%', flexShrink: 0,
            background: 'var(--color-surface)', border: `4px solid ${TIER_COLORS[tier]}`,
            display: 'grid', placeItems: 'center', textAlign: 'center',
          }}
        >
          <span style={{ fontSize: 15, fontWeight: 700, color: TIER_COLORS[tier] }}>{tier}</span>
        </div>
      </div>

      {/* Three summary mini-cards -- same rhythm as the reference's
          Symptoms/Duration/Risk Score row, using only real fields we
          actually have (no invented "risk score out of 10"). */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 'var(--space-6)' }}>
        <MiniCard
          label="Symptoms Reported"
          value={submittedSymptoms.length || '—'}
          accent="var(--color-teal)"
        />
        <MiniCard
          label="Diagnoses Considered"
          value={triage.differential_diagnosis?.length ?? 0}
          accent="var(--tier-orange)"
        />
        <MiniCard
          label="Top Match Confidence"
          value={topMatch ? `${(topMatch.probability * 100).toFixed(0)}%` : '—'}
          accent="var(--tier-red)"
        />
      </div>

      {submittedSymptoms.length > 0 && (
        <div style={{ fontSize: 13, color: 'var(--color-ink-muted)', marginTop: -8, marginBottom: 'var(--space-6)' }}>
          Reported: {submittedSymptoms.join(', ')}
        </div>
      )}

      {triage.red_flag_alerts?.length > 0 && (
        <Section title="Red Flag Alerts">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {triage.red_flag_alerts.map((flag) => (
              <div
                key={flag}
                style={{
                  background: 'var(--tier-red-bg)', color: 'var(--tier-red)',
                  padding: '8px 12px', borderRadius: 'var(--radius-sm)', fontSize: 13, fontWeight: 600,
                }}
              >
                ⚠ {flag}
              </div>
            ))}
          </div>
        </Section>
      )}

      <Section title="Differential Diagnosis">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {triage.differential_diagnosis.map((d) => (
            <div key={d.disease} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 160, fontSize: 13 }}>{d.disease}</div>
              <div style={{ flex: 1, background: 'var(--color-border)', borderRadius: 999, height: 8 }}>
                <div
                  style={{
                    width: `${d.probability * 100}%`, background: 'var(--color-teal)',
                    height: '100%', borderRadius: 999,
                  }}
                />
              </div>
              <div style={{ width: 50, fontFamily: 'var(--font-mono)', fontSize: 12, textAlign: 'right' }}>
                {(d.probability * 100).toFixed(1)}%
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Suggested Care Pathway">
        <div style={{ fontSize: 14 }}>{triage.suggested_care_pathway}</div>
      </Section>

      <button onClick={() => navigate('/intake')} style={linkButtonStyle}>
        Start a new assessment
      </button>
    </div>
  )
}

function MiniCard({ label, value, accent }) {
  return (
    <div style={{
      flex: 1, background: 'var(--color-surface)', border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius)', padding: 'var(--space-4)',
    }}>
      <div style={{ fontSize: 11, color: 'var(--color-ink-muted)', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700, color: accent, fontFamily: 'var(--font-mono)' }}>{value}</div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div
      style={{
        background: 'var(--color-surface)', border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius)', padding: 'var(--space-6)', marginBottom: 'var(--space-6)',
      }}
    >
      <h3 style={{ fontSize: 15, marginBottom: 'var(--space-4)' }}>{title}</h3>
      {children}
    </div>
  )
}

const linkButtonStyle = {
  background: 'none', border: '1px solid var(--color-teal)', color: 'var(--color-teal)',
  borderRadius: 'var(--radius-sm)', padding: '10px 20px', fontWeight: 600, fontSize: 13,
}
