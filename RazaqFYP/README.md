# HANS-Triage

Disease Symptom-Based Triage and Clinical Decision Support System
Final Year Project — Ibrahim Abdulrazaq, Computer Science, ATBU Bauchi

## Current status: Phases 0-9 substantially complete (of 10). Live-testing and refinement ongoing.

See **docs/PROGRESS.md** for the full, honest build log — what's done,
what's stubbed, what's been tested vs. what's only been reviewed carefully.

See **docs/SETUP.md** for the one-time setup, then:

```
npm run dev
```

from the project root starts BOTH the backend and frontend together, in
one terminal. Open http://localhost:5173. (`npm start` builds and runs
everything as a single server on http://localhost:8000 instead — useful
for defense day.)

## What's built so far

- **Phase 0** — Project structure, environment (Docker/Python 3.11/Git),
  real vignette dataset (IyàwóBench v1.0, 200 cases), 5-level triage
  taxonomy mapped from the dataset's native 3-level scheme.
- **Phase 1** — Clinical entity extraction (symptom/negation/duration/
  severity), rule/dictionary-based rather than BioMistral-7B (no GPU
  available) — see docs/PROGRESS.md for why. SNOMED CT terminology mapping.
- **Phase 2** — Per-disease Bayesian diagnosis engine + WHO IMCI-based
  deterministic safety rules + hybrid combination logic. Evaluated against
  all 200 real vignettes: 0% under-triage, QWK 0.596 (with an honest
  caveat about needing a held-out train/test split before final reporting
  — see docs/PROGRESS.md).
- **Phase 3** — Multi-agent orchestration (Symptom/Diagnosis/Triage agents
  real; Interaction/Chat agents are labeled stubs pending real data/API
  key) with genuinely demonstrated error isolation. FastAPI web layer.
- **Phase 4** — PostgreSQL + MongoDB schema design, RBAC, immutable audit
  logging. Validated via testable stand-ins (SQLite, in-memory) since no
  live DB servers are available in the build environment.

## What's next

- **Phase 5** — Vision Agent (image-based rash/inflammation analysis)
- **Phase 6** — HL7/FHIR interoperability
- **Phase 7** — Frontend (design references from supervisor already saved
  in docs/design_references/, ready to use when we get here)
- **Phase 8** — Full validation & evaluation (proper train/test split)
- **Phase 9** — Documentation & defense prep

## Folder structure

```
package.json      <- run `npm run dev` / `npm start` from here (project root)
tools/            <- small launcher scripts behind the npm commands above
backend/
  app/
    agents/       <- Symptom, Diagnosis, Triage, Interaction, Chat agents
    db/           <- PostgreSQL + MongoDB schemas, RBAC, audit logging
    main.py       <- FastAPI application entry point
    orchestrator.py
  tests/          <- Evaluation scripts
  requirements.txt
  .env.example    <- copy to backend/.env, fill in your DB password
frontend/
  src/
    pages/        <- Login, SignUp, Intake, Result, Dashboard, Admin
    components/   <- Layout, StepProgress, ToggleSwitch
    api/          <- client.js, talks to the backend
data/
  raw/            <- Original IyàwóBench dataset
  processed/      <- CPTs, tier distributions, mapped triage data
docs/
  PROGRESS.md     <- Full build log, read this first
  SETUP.md        <- What to install/run locally, in order
  design_references/  <- Supervisor's UI mockups, for Phase 7
scripts/          <- One-off data processing scripts
```
