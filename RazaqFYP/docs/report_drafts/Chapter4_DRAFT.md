# CHAPTER FOUR: SYSTEM DESIGN AND IMPLEMENTATION (DRAFT)

*This replaces the original Chapter Four. Where the implementation
deliberately departs from the original proposal, the reason is stated
explicitly rather than silently changed — a panel is far more comfortable
with a justified scope decision than an unexplained gap.*

## 4.1 System Overview

HANS-Triage was implemented as a modular multi-agent clinical decision
support system, built and tested incrementally across ten development
phases. The system was developed solo, under significant timeline
constraints, which shaped several deliberate architectural and scope
decisions documented throughout this chapter — each decision is stated
with its reasoning, not hidden.

## 4.2 Departures from the Original Proposal (and why)

| Proposed | Implemented | Reason |
|---|---|---|
| BioMistral-7B clinical NLP | Rule/dictionary-based symptom extractor | No GPU available for a 7B-parameter model at usable speed; the system's actual symptom vocabulary is closed and small (14 symptoms), making a dictionary approach comparably effective at a fraction of the complexity. The supervisor's own UI reference designs also show checkbox-based symptom entry as the primary intake method, reducing reliance on free-text NLP. |
| Per-malady Bayesian Networks (implied: full graphical model library) | Pure-Python Naive Bayes implementation | No external ML library dependency required; fully auditable, every inference step traceable — directly serving the proposal's own "auditable decision trail" requirement. |
| Multi-agent microservices (separate deployable services) | Modular monolith: isolated Python modules with a defined interface, orchestrated in-process | True containerized microservices are disproportionate engineering overhead for this scale and timeline; module boundaries and error isolation (see 4.5) preserve the *design property* the proposal calls for without the deployment complexity. |
| Interaction Agent (full drug-interaction database) | Labeled stub with a small demonstration table | No medication/allergy data exists in the training dataset; a real implementation needs a licensed clinical drug-reference source, out of scope for this timeline. |
| Chat Agent (Claude API) | Interface built, real API call written but inactive by default | Requires a user-supplied API key; the interface and call code are complete and activate immediately once a key is set. |
| MongoDB (conversational data) | Schema designed and logic-tested; live instance not installed | Its only consumer (Chat Agent) is a stub with no real conversation data yet — installing a live database with nothing to store would not have added genuine value. |
| Full authentication system | Demo login (no credential verification) | Users/roles tables exist in the PostgreSQL schema; the login UI is built; credential verification against the database was not completed within the available timeline. |

## 4.3 System Architecture

*(Insert your system architecture diagram here — the agent boundary
diagram from docs/design_references or a fresh one showing: Symptom
Agent → Diagnosis Agent → Rule Engine → Hybrid Engine → Triage Agent,
with Interaction/Chat/Vision agents as parallel, isolated branches.)*

The system is composed of the following agents, each implemented as an
isolated Python module with a defined function-call interface:

- **Symptom Agent** — extracts symptoms, negation, duration, and severity
  from free-text input (backend/app/agents/nlp_extractor.py), and maps
  extracted entities to SNOMED CT terminology.
- **Diagnosis Agent** — computes a probability-ranked differential
  diagnosis using per-disease Naive Bayes networks
  (backend/app/agents/bayesian_diagnosis.py).
- **Rule Engine** — encodes WHO IMCI and Surviving Sepsis Campaign
  danger-sign criteria as deterministic safety-floor rules
  (backend/app/agents/rule_engine.py).
- **Hybrid Engine** — combines the Diagnosis Agent's probabilistic
  output with the Rule Engine's safety floor: `final_tier =
  max(bayesian_suggested_tier, rule_floor_tier)`, ensuring rules can only
  make the outcome *more* urgent, never less (backend/app/agents/hybrid_engine.py).
- **Triage Agent** — formats the final decision into the structured
  output specified in the original proposal (5-level color-coded tier,
  rationale, differential list, red-flag alerts, care pathway).
- **Vision Agent** — analyzes uploaded skin-condition images using a
  redness-index heuristic (2R−G−B per pixel), feeding a red-flag signal
  into the Rule Engine when significant redness is detected.
- **Interaction Agent** and **Chat Agent** — stubs, see 4.2.

## 4.4 Data Foundation

The system uses IyàwóBench v1.0, a real, licensed (CC BY 4.0) dataset of
200 febrile-illness triage vignettes derived from Oyo State, Nigeria
primary health center data, covering 8 disease categories: Uncomplicated
Malaria, Severe Malaria, Cerebral Malaria, Typhoid Fever, Bacterial
Meningitis, Sepsis, Pneumonia, and Severe Pneumonia. This dataset was
selected in place of the originally proposed Asclepius and King Fahad
Hospital sources — during development, Asclepius was found to be a
clinical language-model training set (synthetic discharge summaries), not
a triage vignette dataset, and no public "King Fahad Hospital open
dataset" for triage could be located. IyàwóBench provides real,
guideline-referenced (WHO IMCI, WHO Malaria Guidelines, Surviving Sepsis
Campaign, Nigeria STG) triage labels and vitals, and was judged a better
fit given the system's Nigerian deployment context.

The dataset's native 3-level triage scheme (REFER_NOW / REFER_TODAY /
TREAT_HERE) was mapped to the proposal's 5-level ESI/MTS-style scheme
(Red/Orange/Yellow/Green/Blue) using a documented, rule-based mapping
(scripts/map_triage_5level.py) grounded in WHO IMCI danger-sign criteria,
with vital-sign safety-net overrides.

## 4.5 A Demonstrated Safety Property

A central design goal — stated in the proposal's Chapter 4.2 as a
"safety-first conservative bias" — was tested directly, not just claimed.

**Example case:** a patient presenting with only mild fatigue (no other
reported symptoms) but a dangerously low oxygen saturation (SpO2 = 84%).

- The Bayesian diagnosis engine alone, reasoning purely from symptoms,
  suggested a "Yellow" (Urgent) tier.
- The Rule Engine's vital-sign safety net detected the hypoxic SpO2
  reading and set a "Red" (Immediate) floor.
- The Hybrid Engine's `max()` combination correctly produced a final
  "Red" classification.

This demonstrates, concretely, that the hybrid architecture catches
danger signs a purely probabilistic model would miss — directly
validating the design rationale in Chapter Two's literature review.

**Error isolation** was similarly tested, not just designed: a simulated
Interaction Agent failure (a forced exception) was confirmed not to
prevent the Triage Agent from completing successfully, and the failure
was captured and surfaced rather than crashing the request.

## 4.6 Error Handling and Auditability

Every triage decision includes an explicit, human-readable rationale
trail (e.g., *"Bayesian model suggested 'Orange'... Rule engine floor was
'Red' (triggered by: SpO2 84% < 90%)... Final tier = max(both) = 'Red'."*),
satisfying the CDSS Reference Model's "historical decision bias
mitigation" and "mimic cognitive processes" requirements discussed in
Chapter Two.

An append-only audit log (PostgreSQL `audit_log` table) records every
decision with a SHA-256 input hash for tamper detection. Immutability is
enforced at two levels: the application-level `AuditLogger` class has no
update/delete method at all, and the database role's UPDATE/DELETE
privileges on the table are revoked directly in PostgreSQL.

## 4.7 Frontend

A React (Vite) frontend was built matching the supervisor's provided
design references: a teal-branded login screen, a multi-step symptom/vitals
intake wizard with toggle-switch symptom selection, and a diagnosis result
page using the 5-level triage color spectrum as its central design
element. A persistent advisory disclaimer banner ("This system provides
advisory decision support only...") is displayed on every page, satisfying
the ethical requirement stated in the proposal's Chapter 3.10.

## 4.8 Known Limitations (stated explicitly)

- The Vision Agent's redness threshold is uncalibrated against real
  clinical images (none were available); testing revealed it can
  over-flag pale/light skin tones due to the specified formula's
  sensitivity to overall brightness. Documented as required future work.
- The FHIR integration targets a public test sandbox with documented
  uptime issues; not suitable as a production interoperability claim
  without a dedicated/licensed FHIR server.
- Triage decisions are not yet persisted to the database from the live
  API — the schema and write logic exist, but the endpoint does not yet
  call them.
- The 200-vignette dataset, while real and licensed, is modest in size;
  held-out test results (Chapter Five) should be read as an early,
  promising signal rather than a precise population estimate.
