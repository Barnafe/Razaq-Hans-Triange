// API client for the HANS-Triage backend.
//
// Uses relative paths with NO prefix, so this works identically in both:
//   - Dev mode (two servers): vite.config.js proxies these exact paths
//     to http://localhost:8000
//   - Production/single-server mode: FastAPI serves the built frontend
//     AND the API from the same origin, so relative paths just work,
//     no proxy needed at all.
// This was restructured after real user feedback that a two-terminal,
// proxied dev setup was causing confusion and friction -- see docs/SETUP.md
// "Running as ONE server" section for the single-command way to run this.

const BASE = ''

export async function submitTriage(payload) {
  const res = await fetch(`${BASE}/triage`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    throw new Error(`Triage request failed: HTTP ${res.status}`)
  }
  return res.json()
}

export async function login(username, password) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    // The backend sends a structured detail object (not a plain string)
    // specifically for the "correct password, unverified email" case,
    // so the login page can drop the user straight into the verify-code
    // flow instead of just showing a dead-end error.
    if (body.detail && typeof body.detail === 'object' && body.detail.error === 'email_not_verified') {
      const err = new Error('Please verify your email before signing in.')
      err.code = 'email_not_verified'
      err.email = body.detail.email
      throw err
    }
    throw new Error(body.detail || `Login failed: HTTP ${res.status}`)
  }
  return res.json()
}

export async function register(username, password, role = 'clinician', email = null) {
  const res = await fetch(`${BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, role, email }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Registration failed: HTTP ${res.status}`)
  }
  return res.json()
}

export async function verifyEmail(email, code) {
  const res = await fetch(`${BASE}/auth/verify-email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, code }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Verification failed: HTTP ${res.status}`)
  }
  return res.json()
}

export async function resendVerification(email) {
  const res = await fetch(`${BASE}/auth/resend-verification`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: HTTP ${res.status}`)
  }
  return res.json()
}

export async function forgotPassword(email) {
  const res = await fetch(`${BASE}/auth/forgot-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed: HTTP ${res.status}`)
  }
  return res.json()
}

export async function resetPassword(token, newPassword) {
  const res = await fetch(`${BASE}/auth/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, new_password: newPassword }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Reset failed: HTTP ${res.status}`)
  }
  return res.json()
}

export async function getAllUsers() {
  const res = await fetch(`${BASE}/admin/users`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Could not load users: HTTP ${res.status}`)
  }
  return res.json()
}

export async function getRecentEncounters(limit = 20) {
  const res = await fetch(`${BASE}/encounters/recent?limit=${limit}`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Could not load recent encounters: HTTP ${res.status}`)
  }
  return res.json()
}

export async function submitVisionCheck(file) {
  const formData = new FormData()
  formData.append('image', file)
  const res = await fetch(`${BASE}/vision-check`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    throw new Error(`Vision check failed: HTTP ${res.status}`)
  }
  return res.json()
}

export async function getAdminDashboardStats() {
  const res = await fetch(`${BASE}/admin/dashboard-stats`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Could not load dashboard stats: HTTP ${res.status}`)
  }
  return res.json()
}

export async function getPendingReviews() {
  const res = await fetch(`${BASE}/admin/pending`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Could not load pending reviews: HTTP ${res.status}`)
  }
  return res.json()
}

export async function getAvailableDoctors() {
  const res = await fetch(`${BASE}/admin/doctors/available`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Could not load available doctors: HTTP ${res.status}`)
  }
  return res.json()
}

export async function approveDecision(decisionId, doctorId, adminUserId) {
  const res = await fetch(`${BASE}/admin/decisions/${decisionId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ doctor_id: doctorId, admin_user_id: adminUserId }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Approve failed: HTTP ${res.status}`)
  }
  return res.json()
}

export async function rejectDecision(decisionId, adminUserId, reason) {
  const res = await fetch(`${BASE}/admin/decisions/${decisionId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ admin_user_id: adminUserId, reason }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Reject failed: HTTP ${res.status}`)
  }
  return res.json()
}

export async function getAssignedDecisions(doctorId) {
  const res = await fetch(`${BASE}/doctor/assigned?doctor_id=${doctorId}`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Could not load assigned patients: HTTP ${res.status}`)
  }
  return res.json()
}

export async function markAttended(decisionId, doctorId) {
  const res = await fetch(`${BASE}/doctor/decisions/${decisionId}/attend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ doctor_id: doctorId }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Could not mark attended: HTTP ${res.status}`)
  }
  return res.json()
}

export async function getPatientHistory(patientUserId) {
  const res = await fetch(`${BASE}/patient/history?patient_user_id=${patientUserId}`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Could not load your history: HTTP ${res.status}`)
  }
  return res.json()
}
