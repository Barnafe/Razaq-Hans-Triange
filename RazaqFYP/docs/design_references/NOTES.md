# Frontend Design References (from supervisor)

Saved in this folder for use during Phase 7 (Frontend & Integration). Notes on
what each shows, so we don't have to re-view images later:

- **login_reference.jfif** — Clean split login screen (teal/white), email +
  password fields, "Continue with Google" option, medical iconography (DNA,
  stethoscope, heartbeat line).

- **dashboard_reference.jfif** — Clinician-facing dashboard with sidebar nav
  (Dashboard/Doctors/Appointment/Patients/Staff/Department/Payment/Chat/
  Settings). Top cards: High Risk Today, Appointment Today, Risk Today,
  Inactive Patients, Normal, RPM Enrolment. Center donut chart "Post-Op
  Follow Up". Right column: Symptoms Reported table, Recent Activity feed.

- **admin_dashboard_reference.jfif** — Admin/hospital-ops dashboard, dark
  theme, sidebar (Dashboard/Patient Mgmt/Doctor Mgmt/Appointments/Billing/
  Pharmacy/Medical Records/Staff). Top stat cards: Total Patients,
  Appointments Today, Available Doctors, Revenue. Line chart (Patient
  Admissions), donut chart (Department Popularity), Quick Links, Recent
  Activity feed.

- **symptoms_form_reference.jfif** — Multi-step wizard form ("Healthdesk"):
  Identification -> Personal data -> Symptoms -> Additional info ->
  Healthcheck -> Severity -> Done. Symptoms step shows a 0-10 severity
  slider + toggle-switch checklist of symptoms (two columns).

- **diagnosis_result_reference.jfif** — "MediCore AI" patient-facing result
  page. Step progress bar (Symptoms/Severity/Duration/Vital Signs/Medical
  History/Assessment Result). Result card shows Urgency Level (e.g.
  "Medium"), a numeric risk score (e.g. 6/10), explanation text, and
  sub-cards for Symptoms/Duration/Risk Score. Privacy badge footer
  (encrypted/HIPAA/no data retention).

- **patient_history_reference.jfif** — Plain-text description (not a visual
  mockup) of the intake page: healthcare worker enters patient name, age,
  gender, temperature, duration of illness, and selects symptoms via
  checkboxes (Fever, Headache, Cough, Vomiting, Diarrhea, Body pain,
  Fatigue, Chest pain, Difficulty breathing), then clicks "Analyze
  Symptoms".

- **health_history_form_reference.png** — Tablet-style "Health History
  Questionnaire": reason for visit (free text), current medications table
  (name/frequency/dosage, add-row button), and a large checkbox grid of
  past medical history conditions.

## How we'll use these
When we reach Phase 7, each of these maps to a screen in HANS-Triage:
- login_reference -> our login screen
- dashboard_reference / admin_dashboard_reference -> clinician/admin
  dashboard (adapt cards to triage-relevant stats, not hospital billing/etc.)
- symptoms_form_reference / patient_history_reference -> our symptom +
  vitals intake form
- diagnosis_result_reference -> our triage output / assessment result screen
- health_history_form_reference -> optional patient history/medication
  intake, if time allows in scope
