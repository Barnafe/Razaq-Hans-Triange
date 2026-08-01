import React from 'react'

// Step progress indicator matching the supervisor's symptoms_form_reference
// design: connected circular step markers, teal for completed/current,
// gray for upcoming.
export default function StepProgress({ steps, currentIndex }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', marginBottom: 'var(--space-8)' }}>
      {steps.map((label, i) => {
        const isDone = i < currentIndex
        const isCurrent = i === currentIndex
        const color = isDone || isCurrent ? 'var(--color-teal)' : '#C7CFD6'

        return (
          <React.Fragment key={label}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <div
                style={{
                  width: 32, height: 32, borderRadius: '50%',
                  border: `2px solid ${color}`,
                  background: isCurrent ? 'var(--color-teal-light)' : 'transparent',
                  display: 'grid', placeItems: 'center',
                  color, fontSize: 13, fontWeight: 600,
                }}
              >
                {isDone ? '✓' : i + 1}
              </div>
              <span style={{ fontSize: 11, color, fontWeight: isCurrent ? 600 : 400, whiteSpace: 'nowrap' }}>
                {label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div style={{ flex: 1, height: 2, background: isDone ? 'var(--color-teal)' : '#E2E8EC', margin: '0 4px 20px' }} />
            )}
          </React.Fragment>
        )
      })}
    </div>
  )
}
