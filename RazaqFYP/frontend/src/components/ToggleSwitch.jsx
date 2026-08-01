import React from 'react'

// Accessible toggle switch (real checkbox input, styled as a switch) --
// matches the visual style of the supervisor's symptoms_form_reference,
// but keeps proper keyboard/screen-reader support rather than a fake
// div-only toggle.
export default function ToggleSwitch({ checked, onChange, label }) {
  return (
    <label
      style={{
        display: 'flex', alignItems: 'center', gap: 12,
        fontSize: 14, cursor: 'pointer', userSelect: 'none',
      }}
    >
      <span
        style={{
          position: 'relative', width: 40, height: 22, borderRadius: 999,
          background: checked ? 'var(--color-teal)' : '#D6DCE1',
          transition: 'background 0.15s ease', flexShrink: 0,
        }}
      >
        <input
          type="checkbox"
          checked={checked}
          onChange={onChange}
          style={{
            position: 'absolute', inset: 0, opacity: 0, margin: 0, cursor: 'pointer',
          }}
        />
        <span
          style={{
            position: 'absolute', top: 2, left: checked ? 20 : 2,
            width: 18, height: 18, borderRadius: '50%', background: 'white',
            boxShadow: '0 1px 3px rgba(0,0,0,0.3)', transition: 'left 0.15s ease',
            pointerEvents: 'none',
          }}
        />
      </span>
      {label}
    </label>
  )
}
