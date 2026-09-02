import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitTriage, submitVisionCheck } from '../api/client'
import ToggleSwitch from '../components/ToggleSwitch'
import StepProgress from '../components/StepProgress'

// Rebuilt as a multi-step wizard, matching the supervisor's
// symptoms_form_reference design (step progress bar, toggle-switch
// symptom list). HONEST NOTE: the reference includes a 0-10 "how does
// the patient feel overall" slider -- our real backend has no field for
// that, so it's deliberately left out rather than added as a fake,
// disconnected decoration. Every field on every step here is real and
// wired to the actual API.

const SYMPTOMS = [
  'Fever', 'Vomiting', 'Headache', 'Altered consciousness', 'Fatigue',
  'Difficulty breathing', 'Convulsions', 'Loss of appetite', 'Stiff neck',
  'Chest indrawing', 'Joint pain', 'Abdominal pain', 'Diarrhoea', 'Rash',
]

const STEPS = ['Personal Data', 'Vitals', 'Symptoms', 'Image', 'Review']

export default function IntakePage() {
  const [step, setStep] = useState(0)
  const [ageYears, setAgeYears] = useState('')
  const [vitals, setVitals] = useState({
    temperature: '', heart_rate: '', respiratory_rate: '', systolic: '', diastolic: '', spo2: '',
  })
  const [symptoms, setSymptoms] = useState(new Set())
  const [image, setImage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  function toggleSymptom(name) {
    setSymptoms((prev) => {
      const next = new Set(prev)
      next.has(name) ? next.delete(name) : next.add(name)
      return next
    })
  }

  function updateVital(field, value) {
    setVitals((prev) => ({ ...prev, [field]: value }))
  }

  function validateStep() {
    if (step === 0 && !ageYears) return 'Please enter the patient\'s age.'
    if (step === 1) {
      const missing = Object.entries(vitals).find(([, v]) => v === '')
      if (missing) return `Please fill in all vitals (missing: ${missing[0].replace('_', ' ')})`
    }
    return null
  }

  function goNext() {
    const err = validateStep()
    if (err) { setError(err); return }
    setError(null)
    setStep((s) => Math.min(s + 1, STEPS.length - 1))
  }

  function goBack() {
    setError(null)
    setStep((s) => Math.max(s - 1, 0))
  }

  async function handleSubmit() {
    setError(null)
    setLoading(true)
    try {
      let hasVisionRedFlag = false
      if (image) {
        const visionResult = await submitVisionCheck(image)
        hasVisionRedFlag = visionResult.flag
      }

      const role = localStorage.getItem('hans_triage_role')
      const isPatientSelfSubmit = role === 'patient'
      const result = await submitTriage({
        symptoms: Array.from(symptoms),
        temperature: parseFloat(vitals.temperature),
        heart_rate: parseFloat(vitals.heart_rate),
        respiratory_rate: parseFloat(vitals.respiratory_rate),
        systolic: parseFloat(vitals.systolic),
        diastolic: parseFloat(vitals.diastolic),
        spo2: parseFloat(vitals.spo2),
        age_years: parseFloat(ageYears),
        has_vision_red_flag: hasVisionRedFlag,
        self_submitted: isPatientSelfSubmit,
        submitted_by_user_id: isPatientSelfSubmit
          ? parseInt(localStorage.getItem('hans_triage_user_id'), 10)
          : undefined,
      })

      navigate('/result', {
        state: { result, submittedSymptoms: Array.from(symptoms), isPatientSelfSubmit },
      })
    } catch (err) {
      setError(err.message || 'Something went wrong reaching the triage API.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 760 }}>
      <StepProgress steps={STEPS} currentIndex={step} />

      <div
        style={{
          background: 'var(--color-surface)', border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius)', padding: 'var(--space-8)', marginBottom: 'var(--space-6)',
          minHeight: 320,
        }}
      >
        {step === 0 && (
          <StepBlock title="Personal Data" subtitle="Basic information about the patient" icon={<UserIcon />}>
            <VitalField label="Age (years)" value={ageYears} onChange={setAgeYears} />
          </StepBlock>
        )}

        {step === 1 && (
          <StepBlock title="Vitals" subtitle="Enter the patient's current vital signs" icon={<PulseIcon />}>
            {localStorage.getItem('hans_triage_role') === 'patient' && (
              <div
                style={{
                  background: 'var(--color-teal-light)', color: 'var(--color-teal-dark)',
                  fontSize: 12.5, padding: '10px 12px', borderRadius: 'var(--radius-sm)',
                  marginBottom: 'var(--space-4)', maxWidth: 520,
                }}
              >
                These need a real reading (thermometer, pulse oximeter, BP cuff) — please don't
                guess or enter a "normal" placeholder, since that could hide a real danger sign.
                If you don't have a way to measure one of these, note it when you see a doctor.
              </div>
            )}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 'var(--space-4)' }}>
              <VitalField label="Temperature (°C)" value={vitals.temperature} onChange={(v) => updateVital('temperature', v)} />
              <VitalField label="Heart rate (bpm)" value={vitals.heart_rate} onChange={(v) => updateVital('heart_rate', v)} />
              <VitalField label="Respiratory rate" value={vitals.respiratory_rate} onChange={(v) => updateVital('respiratory_rate', v)} />
              <VitalField label="Systolic BP" value={vitals.systolic} onChange={(v) => updateVital('systolic', v)} />
              <VitalField label="Diastolic BP" value={vitals.diastolic} onChange={(v) => updateVital('diastolic', v)} />
              <VitalField label="SpO2 (%)" value={vitals.spo2} onChange={(v) => updateVital('spo2', v)} />
            </div>
          </StepBlock>
        )}

        {step === 2 && (
          <StepBlock title="Symptoms" subtitle="Which symptoms does the patient have?" icon={<ListIcon />}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px 24px' }}>
              {SYMPTOMS.map((s) => (
                <ToggleSwitch key={s} checked={symptoms.has(s)} onChange={() => toggleSymptom(s)} label={s} />
              ))}
            </div>
          </StepBlock>
        )}

        {step === 3 && (
          <StepBlock title="Image" subtitle="Optional: upload a photo of any skin condition" icon={<CameraIcon />}>
            <input
              type="file"
              accept="image/*"
              onChange={(e) => setImage(e.target.files?.[0] || null)}
              style={{ fontSize: 13 }}
            />
            <div style={{ fontSize: 12, color: 'var(--color-ink-muted)', marginTop: 8 }}>
              Analyzed by the Vision Agent for signs of redness/inflammation.
              Heuristic-based, not a trained clinical classifier -- correlate with clinical exam.
            </div>
          </StepBlock>
        )}

        {step === 4 && (
          <StepBlock title="Review" subtitle="Confirm the details below before analyzing" icon={<CheckIcon />}>
            <ReviewRow label="Age" value={`${ageYears} years`} />
            <ReviewRow label="Temperature" value={`${vitals.temperature} °C`} />
            <ReviewRow label="Heart rate" value={`${vitals.heart_rate} bpm`} />
            <ReviewRow label="Respiratory rate" value={vitals.respiratory_rate} />
            <ReviewRow label="Blood pressure" value={`${vitals.systolic}/${vitals.diastolic}`} />
            <ReviewRow label="SpO2" value={`${vitals.spo2}%`} />
            <ReviewRow label="Symptoms" value={Array.from(symptoms).join(', ') || 'None selected'} />
            <ReviewRow label="Image" value={image ? image.name : 'None uploaded'} />
          </StepBlock>
        )}
      </div>

      {error && (
        <div
          style={{
            background: 'var(--tier-red-bg)', color: 'var(--tier-red)',
            padding: 'var(--space-3) var(--space-4)', borderRadius: 'var(--radius-sm)',
            fontSize: 13, marginBottom: 'var(--space-4)',
          }}
        >
          {error}
        </div>
      )}

      <div style={{ display: 'flex', gap: 12 }}>
        {step > 0 && (
          <button onClick={goBack} style={backButtonStyle}>Back</button>
        )}
        {step < STEPS.length - 1 ? (
          <button onClick={goNext} style={nextButtonStyle}>Next step</button>
        ) : (
          <button onClick={handleSubmit} disabled={loading} style={nextButtonStyle}>
            {loading ? 'Analyzing…' : 'Analyze Symptoms'}
          </button>
        )}
      </div>
    </div>
  )
}

function StepBlock({ title, subtitle, icon, children }) {
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
        <div
          style={{
            width: 40, height: 40, borderRadius: '50%', background: 'var(--color-teal-light)',
            display: 'grid', placeItems: 'center', color: 'var(--color-teal)', flexShrink: 0,
          }}
        >
          {icon}
        </div>
        <h2 style={{ fontSize: 22, color: 'var(--color-teal)' }}>{title}</h2>
      </div>
      <p style={{ fontSize: 14, color: 'var(--color-ink-muted)', marginTop: 0, marginBottom: 'var(--space-6)', marginLeft: 52 }}>
        {subtitle}
      </p>
      {children}
    </div>
  )
}

function ReviewRow({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--color-border)', fontSize: 13 }}>
      <span style={{ color: 'var(--color-ink-muted)' }}>{label}</span>
      <span style={{ fontFamily: 'var(--font-mono)' }}>{value}</span>
    </div>
  )
}

function VitalField({ label, value, onChange }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 6, maxWidth: 220 }}>
      <span style={{ fontSize: 12, color: 'var(--color-ink-muted)' }}>{label}</span>
      <input
        type="number"
        step="any"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{
          padding: '8px 10px', borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--color-border)', fontFamily: 'var(--font-mono)', fontSize: 14,
        }}
      />
    </label>
  )
}

const nextButtonStyle = {
  background: 'var(--color-teal)', color: 'white', border: 'none',
  borderRadius: 999, padding: '12px 32px', fontWeight: 600, fontSize: 14,
}

const backButtonStyle = {
  background: 'none', color: 'var(--color-teal)', border: '1px solid var(--color-teal)',
  borderRadius: 999, padding: '12px 32px', fontWeight: 600, fontSize: 14,
}

function UserIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="8" r="4" /><path d="M4 20c0-4.4 3.6-8 8-8s8 3.6 8 8" />
    </svg>
  )
}
function PulseIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="3 12 8 12 10 6 14 18 16 12 21 12" />
    </svg>
  )
}
function ListIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="9" y1="6" x2="20" y2="6" /><line x1="9" y1="12" x2="20" y2="12" /><line x1="9" y1="18" x2="20" y2="18" />
      <circle cx="4" cy="6" r="1.5" fill="currentColor" /><circle cx="4" cy="12" r="1.5" fill="currentColor" /><circle cx="4" cy="18" r="1.5" fill="currentColor" />
    </svg>
  )
}
function CameraIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
      <circle cx="12" cy="13" r="4" />
    </svg>
  )
}
function CheckIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}
