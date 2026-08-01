# DEFENSE PREP — Demo Script & Anticipated Questions

## Before the defense: capture your safety net

**Do this at least once before defense day, while everything is fresh and working:**
1. Screen-record (or screenshot every step of) the full demo flow below,
   successfully completed, on your actual machine.
2. Screenshot a successful FHIR round-trip test result
   (`python scripts/test_fhir_roundtrip.py`) — the public sandbox has
   documented uptime issues, so don't rely on it working live in the room.
3. Save the terminal output of `evaluate_hybrid_engine.py` and
   `evaluate_calibration.py` — these are your real Track B/C results.

Bring the recording as backup. A recorded "here's it working" beats a
live demo failing on unfamiliar WiFi.

## Demo Script (~5-7 minutes)

**1. Open with the safety property, not the tech stack.**
Don't start with "I used FastAPI and PostgreSQL." Start with: *"I want to
show you the core safety mechanism first, then how the system is built."*

**2. Live demo: the ambiguous case.**
Walk through the intake wizard with these values:
- Symptoms: only "Fatigue"
- Temperature: 37.3, HR: 95, RR: 20, Systolic: 105, Diastolic: 68,
  **SpO2: 84**, Age: 60

Before clicking submit, say out loud: *"Notice this patient only reports
mild fatigue — nothing alarming on symptoms alone."* Then submit and show
the result: **Red / Immediate**, and read the rationale aloud — point out
it explicitly says the Bayesian model alone suggested only "Yellow," and
the rule engine's hypoxia check is what escalated it. *This is your
strongest single moment — a concrete proof of the hybrid design working,
not just a claim.*

**3. Show the classic case for contrast.**
Meningitis case (Fever, Headache, Stiff neck, Altered consciousness, high
HR, low-ish SpO2) → Red, with a clean differential diagnosis (Bacterial
Meningitis top, Cerebral Malaria second) — shows the system also handles
"textbook" presentations sensibly, not just edge cases.

**4. Briefly show the architecture, not the code.**
One diagram (build one from Chapter Four's agent list if you don't have
one yet) — Symptom → Diagnosis → Rule Engine → Hybrid → Triage, with
Vision/Interaction/Chat as side branches. Don't scroll through source code
live unless specifically asked.

**5. Close with the honest results.**
State the four real numbers plainly: 0% under-triage (held-out), QWK
0.738, 82.5% diagnosis accuracy, sub-millisecond core latency. Say the
caveats yourself before anyone asks — it reads as rigor, not weakness.

## Anticipated Panel Questions

**"Why didn't you use the LLM you proposed (BioMistral-7B)?"**
No GPU available to run a 7B-parameter model at usable speed; the actual
symptom vocabulary is closed and small, so a rule-based extractor achieves
comparable results at far lower complexity. Mention this was a deliberate,
documented engineering tradeoff, not an oversight.

**"Your QWK is below your proposal's 0.80 target — why?"**
Honest answer: real result on a modest dataset (200 vignettes total, 40
held out). It already beats the ~0.51 manual-triage baseline from your own
literature review. More data would likely tighten this further — name it
as future work, not a failure.

**"How do you know your system isn't just overfitting to this dataset?"**
This is exactly why the 80/20 train/test split exists — the CPTs were
built ONLY from training data, and every reported Track B number is
measured on vignettes the model never saw. Be ready to explain the split
methodology (stratified by disease, fixed seed).

**"What happens if a component fails in production?"**
Point to the demonstrated error-isolation test — a simulated Interaction
Agent crash was shown not to prevent the Triage Agent from completing.
Every agent boundary is isolated by design, not just by intention.

**"Is this system HIPAA compliant / production-ready?"**
No — be direct about this. Deidentification, RBAC, and an immutable audit
log are implemented and tested, which are real steps toward compliance,
but a genuine compliance certification requires formal audit, which is
out of scope for a final year project. Frame it as "compliance-aware
architecture," not "compliant system."

**"Why is under-triage 0% but over-triage 70%?"**
This is a stated, deliberate design tradeoff: the rule floor is
intentionally conservative — it can only push a decision to be MORE
urgent, never less. That guarantees the safety-critical property at the
cost of some false alarms, which is the right tradeoff for a clinical
safety system (a false alarm costs time; a missed emergency costs a
life).

**"What would you do with more time?"**
Have 2-3 ready, pulled from Chapter Five's recommendations: expand the
dataset, calibrate the Vision Agent against real images, wire up database
persistence for a real clinical dashboard.

## What NOT to do
- Don't claim numbers you didn't measure, even under pressure to sound
  more impressive — a caveated real number survives follow-up questions;
  an inflated one doesn't.
- Don't apologize repeatedly for scope cuts — state them once, plainly,
  with the reason, and move on.
- Don't attempt a live FHIR sandbox demo — show the saved screenshot
  instead and say why (documented public server uptime issues).
