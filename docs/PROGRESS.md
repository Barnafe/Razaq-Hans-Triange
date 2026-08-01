# PROGRESS.md — HANS-Triage Build Log

## Phase 0 — Setup & Data Foundation
- [x] Module 0.1a — Project folder structure scaffolded
- [x] Module 0.1b — Environment confirmed: Docker 29.6.2, Git 2.55.0, Python 3.11 installed at C:\Users\USER\AppData\Local\Programs\Python\Python311 (system Python 3.14 left untouched)
- [x] Module 0.2 — Vignette dataset sourced: IyàwóBench v1.0 (200 vignettes, 8 febrile illness categories, real Oyo State PHC-derived data, CC BY 4.0 licensed) loaded into data/raw/iyawobench_v1.csv
- [x] Module 0.3 — Disease shortlist locked (provisional, using real dataset's 8 categories, adjustable if supervisor sends a differing list later): Uncomplicated Malaria, Severe Malaria, Cerebral Malaria, Typhoid Fever, Bacterial Meningitis, Sepsis, Pneumonia, Severe Pneumonia
- [x] Module 0.4 — Triage taxonomy defined: 5-level (Red/Orange/Yellow/Green/Blue) chosen to match original proposal. Rule-based mapping from dataset's native 3-level scheme built in scripts/map_triage_5level.py, applied, output at data/processed/iyawobench_v1_5level.csv (Red:49, Orange:51, Yellow:28, Green:32, Blue:40).

**PHASE 0 COMPLETE.**

## Phase 1 — Clinical NLP Extraction Engine
- [x] Module 1.1 — Approach changed from BioMistral-7B (no GPU available) to a
      dependency-free rule/dictionary extractor, since the real symptom
      vocabulary is closed (14 terms) and supervisor's own UI design shows
      checkbox-based symptom entry as the primary input path anyway. Built
      at backend/app/nlp_extractor.py.
- [x] Module 1.2 — Symptom/negation/duration/severity extraction implemented
      and tested against 4 realistic clinical sentences. Caught and fixed a
      real bug: negation was bleeding across clause boundaries (comma),
      which would have falsely negated a present danger sign ("altered
      consciousness") — fixed by scoping negation search to the current
      clause only.
- [x] Module 1.3 — Mapped all 14 canonical symptoms to real SNOMED CT codes
      (backend/app/terminology_mapper.py). 12/14 codes cross-verified against
      SNOMED International's published docs / NCBO BioPortal this session;
      2 (Stiff neck, Abdominal pain) are high-confidence recall codes
      flagged "reverify" -- quick check against
      https://browser.ihtsdotools.org/ recommended before final report.
- [x] Module 1.4 — Built self-authored 25-sentence labeled eval set
      (backend/app/evaluate_nlp.py). Initial run: F1=0.993, negation
      acc=0.972. Found & fixed 3 real bugs (negation window too narrow for
      "or"-joined lists; "but" not treated as a negation-scope reset;
      missing "weak" synonym for Fatigue). After fixes: F1=1.000, negation
      acc=1.000 on this set.
      CAVEAT for report: this is our own authored test set, not an
      external clinical corpus -- perfect score is expected on data we
      wrote, not proof of real-world accuracy. Phase 8 should test against
      genuinely unseen sentences (ideally written by someone else) for a
      credible reported metric.

**PHASE 1 COMPLETE.**

## Phase 2 — Diagnostic & Triage Core
- [x] Module 2.1 — Built per-malady Bayesian Networks (Naive Bayes, pure Python,
      no pgmpy dependency needed). CPTs built primarily from real vignette data
      (scripts/build_cpt.py), Laplace-smoothed. Found & documented a real
      discrepancy during dev: dataset showed 100% stiff-neck prevalence in
      Bacterial Meningitis; published literature (Medscape/van de Beek cohort)
      puts it at 30-45% -- corrected via a documented 50/50 literature blend
      for that one pair; all other 111 pairs use raw dataset values (full
      literature cross-check of all pairs flagged as a stated limitation, not
      performed -- out of scope for solo timeline). Uniform prior used across
      diseases (not raw sample proportions) since dataset composition reflects
      triage-label balancing, not real epidemiological prevalence -- documented
      in backend/app/bayesian_diagnosis.py. Inference engine tested against 4
      classic textbook presentations -- all correctly identified top diagnosis
      with clinically sensible differentials.
- [x] Module 2.2 — Built deterministic rule layer (backend/app/rule_engine.py):
      WHO IMCI danger-sign rules (convulsions, altered consciousness, SpO2<90,
      systolic<90, resp rate thresholds) -> Red floor; stiff neck, chest
      indrawing, high fever/HR -> Orange floor; difficulty breathing, fever ->
      Yellow floor. Tested against 4 scenarios, behaves as designed (e.g. low
      SpO2 alone escalates to Red even with no other symptoms flagged).
- [x] Module 2.3 — Built hybrid engine (backend/app/hybrid_engine.py):
      final_tier = max(bayesian_suggested_tier, rule_floor_tier). Bayesian
      suggested tier computed via probability-weighted expected urgency across
      differentials, rounded UP (ceiling) for safety bias. Disease->tier
      distribution built from real vignette outcomes (scripts/build_tier_
      distribution.py). KEY RESULT for report: tested an "ambiguous" case
      (only Fatigue reported, but SpO2=84%) -- pure Bayesian alone suggested
      only 'Yellow', but the rule floor correctly forced escalation to 'Red'.
      This is a concrete, demonstrable instance of the safety-first hybrid
      design catching what probabilistic reasoning alone would have missed.
- [x] Module 2.4 — Built Triage Agent output formatter (backend/app/triage_agent.py)
      matching proposal's Chapter 4.7 spec: tier + rationale, differential list,
      red-flag alerts, suggested care pathway.
- [x] Module 2.5 — Evaluated full hybrid pipeline against all 200 real vignettes
      (backend/tests/evaluate_hybrid_engine.py). REAL RESULTS: under-triage rate
      = 0% (safety-critical metric — never told a genuinely urgent case to wait),
      over-triage rate = 70%, exact tier match = 30%, QWK = 0.596 (comparable to
      literature-reported ESI/MTS manual agreement of ~0.51; proposal's target
      was >0.80, not yet met). Honest interpretation for report: rule-floor
      design achieves its core safety goal (zero under-triage) at the cost of
      over-caution — a legitimate, named tradeoff, not a hidden flaw.
      IMPORTANT CAVEAT (flagged in code): this evaluates on the SAME 200
      vignettes the CPTs were built from — not a held-out test set. Required
      before final reporting: build an 80/20 train/test split and re-evaluate
      on unseen vignettes only. Flagged as Phase 8 prerequisite, not yet done.

**PHASE 2 COMPLETE** (core diagnostic/triage logic built, tested, and honestly
evaluated — pending a proper train/test split before numbers go in the report).

## Phase 3 — Multi-Agent Orchestration
- [x] Module 3.1 — Agent boundaries defined: Symptom (nlp_extractor.py), Diagnosis
      (bayesian_diagnosis.py), Triage (triage_agent.py), Interaction (STUB),
      Chat (STUB), Vision (not yet built, Phase 5). Reorganized into
      backend/app/agents/ subdirectory.
- [x] Module 3.2 — Each agent implemented as an isolated Python module with a
      clean function-call interface (not separate deployable microservices --
      documented tradeoff: a modular monolith is realistic for solo/timeline
      constraints, true separate services would need container-per-agent
      orchestration which is disproportionate for this scale). FastAPI web
      layer built (backend/app/main.py) exposing /triage endpoint --
      NOT runtime-tested in this sandbox (no FastAPI/internet here); will be
      first tested when you run it locally per docs/SETUP.md.
- [x] Module 3.3 — Orchestrator built (backend/app/orchestrator.py) with real,
      DEMONSTRATED error isolation: simulated a crashing Interaction Agent,
      confirmed the Triage Agent still completed successfully and the error
      was captured, not propagated. (Caught and fixed a real bug in the test
      harness itself along the way -- first patching attempt silently didn't
      trigger the failure; fixed by correcting the module-namespace patching.)
- [x] Module 3.4 — Chat Agent interface built (backend/app/agents/chat_agent.py),
      designed for the Claude API. Honest status: STUB -- cannot be exercised
      in this build environment (no key/internet here). Real call code is
      written but commented out; activates once you set ANTHROPIC_API_KEY
      locally (see docs/SETUP.md). Interaction Agent also a STUB -- our
      dataset has no medication/allergy fields, so this uses a small labeled
      demonstration table, not a real clinical interaction database.

**PHASE 3 COMPLETE** (core orchestration logic built and tested; FastAPI HTTP
layer written but awaiting first live test on your machine; Chat/Interaction
agents are honest stubs pending real data/API key).

## Phase 4 — Databases & Security/Compliance
- [x] Module 4.1 — PostgreSQL schema written (backend/app/db/schema_postgres.sql):
      roles, users, patients (pseudonymized, not real names), encounters,
      triage_decisions, audit_log. Validated via a SQLite-adapted test
      (backend/app/db/schema_sqlite_test.py) — full insert->join->query flow
      tested, foreign key constraint enforcement confirmed (PASS: invalid
      patient_id insert correctly blocked). Not yet run against a live
      Postgres instance — first test happens on your machine.
- [~] Module 4.2 — MongoDB schema documented and logic-tested (backend/app/db/mongo_schema.py).
      DEFERRED: actual MongoDB installation/live test deliberately postponed --
      its only consumer (Chat Agent) is still a stub with no real conversation
      data to store yet. Revisit when Chat Agent gets a real API key wired up,
      or during Phase 8/9 finalization. Not a blocker for anything else.
- [x] Module 4.3 — RBAC implemented (backend/app/db/rbac_audit.py): role->
      permission mapping (clinician/admin/auditor), tested — correctly
      blocks unauthorized actions. Deidentification handled at schema level
      (patients.pseudonym, not real names).
- [x] Module 4.4 — Immutable audit log implemented, defense-in-depth: (1)
      application-level AuditLogger class has no update/delete method at
      all (confirmed programmatically), (2) documented requirement to also
      revoke UPDATE/DELETE grants on audit_log at the DB level in production
      (SQL for this added to docs/SETUP.md). Tested: logs both normal
      decisions and clinician overrides with justification text.

**PHASE 4 SUBSTANTIALLY COMPLETE.** PostgreSQL schema (4.1) and audit-log
immutability (4.4) are LIVE-VERIFIED against a real PostgreSQL database on
your machine (6 tables created, REVOKE applied successfully). RBAC (4.3)
tested. MongoDB (4.2) deliberately deferred -- see note above, revisit
when Chat Agent needs it for real.

## Phase 5 — Vision Agent
- [x] Module 5.1/5.2 — Redness-index inflammation scoring implemented exactly
      per proposal's formula (2R-G-B per pixel, fraction of significantly red
      pixels = inflammation score). backend/app/agents/vision_agent.py.
      Tested with real Pillow/NumPy image processing (genuinely run, not just
      written) against synthetic test images. FOUND & DOCUMENTED A REAL
      LIMITATION: the fixed threshold (60) is uncalibrated -- a pale pink
      tint (255,220,220) scores as maximum redness (1.0) because R is
      doubled in the formula, so even a small R-vs-G/B gap scores high once
      R itself is bright. This is a genuine weakness of the formula as
      specified, not a bug -- documented clearly in code rather than hidden;
      real calibration needs actual dermatological images we don't have
      access to (stated as required future work).
- [x] Module 5.3 — Wired into diagnosis reasoning: added has_vision_red_flag
      to PatientInput, new rule in rule_engine.py escalates to Orange (not
      Red -- deliberately modest given the calibration limitation above) when
      flagged. Tested end-to-end: same patient vitals/symptoms, tier
      correctly changes Blue -> Orange when vision flag is set, with full
      rationale trail including the honest calibration caveat.
      API: new /vision-check endpoint added to main.py (upload image ->
      get analysis + flag), has_vision_red_flag added to /triage request
      body. Added python-multipart/Pillow/numpy to requirements.txt.
      NOT yet live-tested via the running server (untested-here, same
      pattern as other FastAPI work) -- next thing to test locally.

**PHASE 5 COMPLETE** (core logic built and genuinely tested with real image
processing; API wiring written but pending live test on your machine).

## Phase 6 — HL7/FHIR Interoperability
- [x] Module 6.1 — Verified a real public FHIR sandbox is live (HAPI FHIR
      test server, https://hapi.fhir.org/baseR4, confirmed via direct fetch
      during dev -- real response headers seen). HONEST CAVEAT found during
      research: this server has documented uptime issues (a GitHub issue
      titled "HAPI FHIR's Public Test Server is Down" exists from earlier
      this year) -- do NOT rely on live internet access to it during your
      actual defense. Capture a screenshot of a successful test now.
- [x] Module 6.2 — Built real FHIR R4-compliant resource construction
      (backend/app/agents/fhir_integration.py): Patient (deidentified,
      pseudonym-based) + Observation (triage tier + differential diagnosis
      as components). Tested locally -- produces valid, well-formed FHIR
      JSON. HONEST NOTE: the triage-tier coding system used is a CUSTOM
      code (not a real published LOINC/SNOMED standard, since no such
      standard exists for our specific 5-level scheme) -- stated explicitly
      in the resource's own text field, not presented as false standards
      compliance.
- [x] Module 6.3 — Built scripts/test_fhir_roundtrip.py: submits a real
      Patient+Observation to the live sandbox, reads it back, verifies the
      round-trip. NOT yet run against the live server (needs internet,
      which this build sandbox doesn't have) -- next thing to test locally,
      alongside the Phase 5 vision endpoint.

**PHASE 6 COMPLETE** (resource construction tested and valid; live network
round-trip written and ready, pending your local test run).

## Phase 7 — Frontend & Integration
- [x] Module 7.1 — React (Vite) intake form built: checkbox symptom selection
      (matching real 14-symptom vocabulary from our NLP/Bayesian engine, and
      matching supervisor's checkbox-based design reference), vitals inputs,
      optional image upload wired to Vision Agent. Design grounded in
      supervisor's actual references (teal branding, dark sidebar) rather
      than generic AI-template look -- design tokens documented in
      frontend/src/tokens.css. All JSX files verified for real syntax
      errors using `tsx` (Node.js + esbuild, available in this sandbox) --
      genuinely checked, not just assumed correct.
- [x] Module 7.2 — Diagnosis result page built: the 5-level triage color
      spectrum used as the actual design signature (not decoration -- it's
      the system's real output), differential diagnosis bars, red-flag
      alerts, care pathway. HONEST GAP FOUND: our /triage endpoint never
      actually persists to the PostgreSQL database built in Phase 4 --
      it computes and returns a result but doesn't INSERT anything. This
      means a "dashboard of past decisions" would have no real data --
      deliberately NOT built to avoid faking data. Flagged as needed
      backend wiring, likely in Phase 8/9 cleanup.
- [x] Module 7.3 — Frontend wired to the real backend API (fetch calls to
      /triage and /vision-check, via a Vite dev-server proxy to
      localhost:8000). NOT yet rendered in an actual browser (no npm
      install possible in this sandbox, no internet) -- syntax-verified
      only. First real render happens on your machine.
- [x] Module 7.4 — Added the proposal's REQUIRED persistent clinical
      disclaimer banner (Chapter 3.10: "advisory decision support only,
      not a replacement for clinical judgment") -- this was a stated
      requirement, not optional polish, so added deliberately rather than
      left for later. Login page is honestly labeled as a demo, not
      connected to real authentication (users/roles tables exist in
      Postgres from Phase 4, but nothing checks credentials yet).

**PHASE 7 SUBSTANTIALLY COMPLETE.** Core flow (login -> intake -> result)
built and wired to the real backend, syntax-verified. Awaiting: (1) first
actual browser render on your machine, (2) DB persistence wiring so a
real dashboard becomes possible later, (3) real authentication.

## Phase 8 — Validation & Testing
- [x] Module 8.2 — Built genuine 80/20 stratified train/test split
      (scripts/train_test_split.py, seed=42, every disease represented in
      both sets despite small classes like Cerebral Malaria n=10).
      Rebuilt CPTs and tier distribution from the 160 TRAINING vignettes
      only. Re-ran evaluate_hybrid_engine.py against the 40 HELD-OUT test
      vignettes the model never saw during training. REAL RESULTS:
      under-triage rate STILL 0% (safety property held under genuine
      generalization testing, not just memorization), QWK = 0.738 (up
      from the earlier non-independent 0.596, and now clearly ahead of
      the ~0.51 kappa the proposal's own literature review cites for
      manual ESI/MTS agreement -- still short of the proposal's >0.80
      target). HONEST CAVEAT: 40 test examples (as few as 2 for Cerebral
      Malaria) is a small sample -- report as a promising signal, not a
      precise estimate. This result is now genuinely reportable in
      Chapter 5, unlike the earlier self-consistency numbers.
- [x] Module 8.3 — Latency benchmarking (backend/tests/benchmark_latency.py):
      500 runs of the full diagnostic/triage core. Mean 0.134ms, P99 0.279ms
      -- comfortably PASSES the proposal's <2.5s requirement. HONEST CAVEAT
      stated in the script itself: this measures the computational core
      only (pure Python), not full HTTP/DB/network round-trip -- a lower
      bound, not the complete production picture.
- [x] Module 8.4 — Expected Calibration Error (backend/tests/evaluate_calibration.py),
      computed on the same held-out test set as Module 8.2. REAL RESULTS:
      82.5% top-1 diagnosis accuracy (distinct from the 30% triage-TIER
      exact match -- this measures "did it pick the right disease"), ECE =
      0.126, with the model's highest-confidence bin being slightly
      UNDERconfident (91.5% avg confidence vs 100% actual accuracy) -- the
      safer direction to be miscalibrated in. HONEST CAVEAT: lowest-
      confidence bin only had 3 samples, too small to trust as a precise
      number.

**PHASE 8 SUBSTANTIALLY COMPLETE.** All four tracks now have real,
held-out, honestly-caveated results suitable for Chapter 5 -- a major
upgrade from the earlier non-independent self-consistency numbers.
Remaining: Module 8.1's NLP test set is still self-authored (lower
priority given time constraints -- flagged, not blocking).

## Phase 9 — Documentation & Defense Prep
- [x] Module 9.1 — Drafted replacement Chapter 4 and Chapter 5
      (docs/report_drafts/Chapter4_DRAFT.md, Chapter5_DRAFT.md). Chapter 5
      is the critical fix: the ORIGINAL uploaded proposal's Chapter 5
      contained fabricated results (F1=0.84, QWK=0.88, 35->28 min latency
      claims) that were never real -- flagged all the way back at project
      start. New draft uses ONLY real Phase 8 held-out numbers, every
      figure traceable to an actual test run. Chapter 4 documents every
      proposal departure with its reason in a table, plus the demonstrated
      safety-property example and known limitations.
- [x] Module 9.2/9.3 — Built docs/report_drafts/DEFENSE_PREP.md: demo
      script (leads with the SpO2-84%-ambiguous-case safety demo, not the
      tech stack), pre-defense safety-net checklist (screen-record before
      defense day, don't rely on live FHIR sandbox), and anticipated panel
      Q&A with honest, prepared answers for the hardest questions (why not
      the proposed LLM, why QWK below target, why 70% over-triage, HIPAA
      compliance status).

**PHASE 9 SUBSTANTIALLY COMPLETE.** Report drafts and defense prep exist
and use only real, traceable results. Still needed: user's own review/
edit pass, converting drafts to final report format, building an actual
architecture diagram graphic.

## Live testing log
- **First live run (your machine):** Server booted successfully via
  `uvicorn main:app --reload --port 8000` -- zero setup errors. Real bug
  found on first /triage request: `bayesian_diagnosis.py` and
  `hybrid_engine.py` used relative paths ("data/processed/...") that only
  resolved correctly if the server was started from the project root --
  but since our own setup steps have you `cd app` first, this broke in
  the field. FIXED: both now use absolute paths anchored to the file's own
  location (`os.path.dirname(__file__)`-based), so they work regardless of
  which directory the server is launched from. Verified by re-running from
  `backend/app` (matching your actual setup) -- works correctly now.
  NOTE: this same failure also proved Module 3.3's error isolation works
  in a live, running server, not just in our own tests -- the server
  returned a valid 200 response with the error captured in
  `partial_failures` instead of crashing entirely.

## Frontend live testing log
- **First full end-to-end render (your machine):** Login -> Intake -> real
  POST /triage -> Result page, all working correctly on first real browser
  test. Sidebar, disclaimer banner, tier spectrum bar (correct segment
  highlighted), red flag alerts, differential diagnosis bars, and rationale
  text all rendered correctly. This is the first proof that Phases 0-7 all
  genuinely connect end-to-end, not just individually.
  Setup hiccup along the way (unrelated to our code): pip install failed
  once due to a network timeout mid-download of Pillow/numpy/requests --
  resolved by retrying with a longer --timeout flag.
  KNOWN GAP: Login/Intake/Result visual design does not yet closely match
  supervisor's actual reference mockups (teal split-screen login with
  Google sign-in, etc.) -- functional flow was prioritized first. Next:
  redesign these pages to match his references more closely.

## Frontend design revision
- Rebuilt LoginPage.jsx to closely match supervisor's actual reference
  (teal gradient bg, decorative DNA/stethoscope/heart icon circles, white
  card, "Welcome Back!" heading, email/phone + password fields with icons,
  Forgot Password link, OR divider, Continue with Google button, EKG line
  motif). Still honestly labeled as demo/no real auth.
- Rebuilt IntakePage.jsx as a proper multi-step wizard (Personal Data ->
  Vitals -> Symptoms -> Image -> Review), matching supervisor's
  symptoms_form_reference (step progress bar, toggle-switch symptom list).
  HONEST NOTE: deliberately did NOT add the reference's 0-10 "general
  feeling" slider -- our backend has no field for it, and faking a
  disconnected decorative control was rejected in favor of keeping every
  field on every step genuinely wired to the real API.
- New reusable components: ToggleSwitch.jsx (accessible, real checkbox
  input styled as a switch), StepProgress.jsx (step indicator).
- All new/changed files syntax-verified with tsx -- no errors.
- STILL NOT rendered in an actual browser since this revision -- next
  local test needed.

## Gap-closing batch: persistence, real auth, dashboard
- [x] Database persistence — backend/app/db/connection.py (psycopg2
      connection helper, reads HANS_DB_PASSWORD env var) and
      backend/app/db/persistence.py (writes patient -> encounter ->
      triage_decision -> audit_log per real request). Wired into /triage
      in main.py with graceful degradation: a persistence failure is
      captured in partial_failures, never breaks the actual triage
      response (same error-isolation philosophy as the orchestrator).
      New GET /encounters/recent endpoint for the dashboard.
- [x] Real authentication — backend/app/db/auth.py: PBKDF2-HMAC-SHA256
      password hashing (stdlib only, no new dependency), real credential
      check against the users table, timing-attack-resistant (dummy hash
      computed even when username doesn't exist). New POST /auth/login
      endpoint. scripts/seed_demo_user.py creates a real demo user
      (nurse_amina). LoginPage.jsx now calls the real endpoint -- wrong
      passwords genuinely fail now. HONEST SCOPE NOTE: no session/token
      issued after login yet -- flagged as the next real step in
      auth.py's docstring, not silently skipped.
- [x] Real dashboard — DashboardPage.jsx fetches actual persisted
      encounters via GET /encounters/recent, shows real tier-count
      summary cards and a real recent-assessments table. Deliberately
      does NOT show fake stats (revenue, staff counts) from the generic
      hospital-admin reference image, since there's no real data source
      for those in this system.
- All new/changed files syntax-verified (Python via py_compile, JS/JSX
  via tsx) -- zero errors. NOT yet live-tested (needs psycopg2 install +
  HANS_DB_PASSWORD set + seed script run on your machine) -- next local
  test batch.
- MongoDB remains deliberately deferred -- still true that its only
  consumer (Chat Agent) is a stub with nothing real to store.

## Wiring fix + PowerShell syntax bug fix (real user-reported issues)
- **Wiring gap owned and fixed:** user's original requirement (stated
  back at Phase 3 setup) was for backend+frontend to run as one thing
  from one terminal -- what got built was a standard two-server dev setup
  instead, which was never explicitly flagged as a deviation at the time.
  FIXED: FastAPI now serves the built frontend directly (StaticFiles +
  SPA fallback route in main.py), frontend API client restructured to use
  relative paths with no prefix (works unchanged in both dev-proxy and
  single-server modes), vite.config.js updated to proxy specific paths
  instead of a generic /api prefix. `npm run build` + one `uvicorn`
  command now serves the ENTIRE app on localhost:8000. Two-terminal dev
  mode kept as an documented optional path for active frontend editing
  only, not the default.
- **Real bug found via user's live testing:** SETUP.md used cmd.exe `set
  VAR=value` syntax throughout, but the user has been in PowerShell the
  entire time (visible in every terminal paste) -- that syntax doesn't
  set a real environment variable in PowerShell, causing
  "HANS_DB_PASSWORD not set" errors even after "setting" it. FIXED: all
  instances corrected to PowerShell's `$env:VAR = "value"` syntax.
  HONEST NOTE: this was a real mistake in the instructions I gave,
  caught by the user pushing back and asking directly whether this had
  actually been tested -- it hadn't (no live PostgreSQL in the build
  sandbox), and this was an honest instruction error, not a fabricated
  "verified working" claim.
- SETUP.md fully restructured into one chronological walkthrough (was
  previously split across two sections in the wrong order, with a
  forward-reference that added confusion).

## Real routing bug found via live testing (single-server mode)
- User navigated to localhost:8000 (correct, single-server mode working)
  but got the raw health-check JSON instead of the login page. ROOT
  CAUSE: the health-check endpoint was registered at the exact path "/",
  which "wins" over the SPA catch-all route that's supposed to serve the
  frontend's index.html at that same path. FIXED: moved health check to
  /health, leaving "/" free for the frontend. GOOD NEWS buried in the
  bug report: the health check response showed "database_available":true
  -- confirms PostgreSQL connectivity, HANS_DB_PASSWORD, and psycopg2 are
  all genuinely working together on the user's machine right now.

## Second gap batch: logout, real registration, styling, dashboard stats
Addressing 4 real points of feedback in one round:
- Logout button added to sidebar (real navigation back to login; honest
  note that no session/token exists yet to actually invalidate -- see
  auth.py).
- Real user registration: POST /auth/register backend endpoint (checks
  username uniqueness, proper password hashing, min 8 chars), new
  SignUpPage.jsx wired to it, LoginPage's "Sign Up" link now actually
  navigates there instead of being dead. This means new clinician
  accounts no longer require manually running the seed script.
- "Continue with Google" now gives an honest on-click explanation
  (requires a registered Google OAuth app, not set up in this build)
  instead of silently doing nothing -- less confusing than a dead button.
- Wizard steps (Personal Data/Vitals/Symptoms/Image/Review) given visual
  icons per step, addressing "still plain white" feedback.
- Dashboard extended with real aggregate stats (total assessments, unique
  patients, average age, most common diagnosis) -- all genuinely computed
  from persisted data, deliberately still NOT showing fake hospital-admin
  metrics (revenue/staff/billing) since no real source exists for those.
- Full syntax sweep across ALL frontend files and ALL backend files --
  zero errors. NOT yet live-tested (needs frontend rebuild + backend
  restart on the user's machine).

## Real bug found via live testing: install:all skipped root's own dependency
- User ran the Quickstart exactly as documented, hit a real error on
  `npm run dev`: `'concurrently' is not recognized as an internal or
  external command`. ROOT CAUSE: `tools/install-all.mjs` installed
  `frontend`'s node_modules and the backend's pip packages, but never
  ran `npm install` at the PROJECT ROOT itself -- so the root
  `package.json`'s own devDependency (`concurrently`, which `npm run
  dev` needs to launch both servers together) was never actually
  installed. FIXED: `install-all.mjs` now runs `npm install` (root)
  first, before the frontend/backend installs. Unblocked live in the
  meantime with a direct `npm install` at the root.
- Confirms `npm run install:all` needs a re-run (or a plain `npm
  install` at the root once) to pick up this fix.

## Real bug found via live testing: JSONB double-deserialization crash
- User's real error, surfaced correctly by the client.js fix above:
  `TypeError: the JSON object must be str, bytes or bytearray, not list`.
- ROOT CAUSE: `symptoms`, `differential_diagnosis`, and `red_flag_alerts`
  are `JSONB` columns in `schema_postgres.sql`. psycopg2 automatically
  deserializes JSONB values into native Python lists/dicts on fetch --
  `get_recent_decisions()` in `persistence.py` was written as if it
  still needed to `json.loads()` those values, which crashes because
  you can't `json.loads()` something that is already a Python list.
  This is a genuine logic bug that syntax-checking (py_compile, esbuild)
  can never catch -- it only shows up against a real, running database,
  which is exactly why it took a live test on the user's machine to
  find, despite thorough syntax verification beforehand.
- FIXED: `get_recent_decisions()` now uses `r[3]` / `r[5]` directly
  instead of `json.loads(r[3])` / `json.loads(r[5])`.
- Swept the rest of the backend for the same mistake: every other
  `json.loads()` call in the codebase was checked -- this was the only
  one reading from a real Postgres JSONB column. The `json.dumps()`
  calls elsewhere are all on the WRITE side (inserting into JSONB
  columns, which correctly accepts a JSON string) or unrelated to the
  database entirely (printing, hashing, the SQLite test harness's own
  TEXT columns) -- none of those needed changing.

## Real bugs found via live testing: BOM in .env, client.js swallowing real error details
- **Confirmed live:** the utf-8-sig fix worked -- once the user's `.env`
  had the correct password, login and registration both succeeded for
  real (verified via `psql` that the password itself was correct; a
  separate one-character typo in `.env` was the last piece, user fixed
  it directly).
- **Real bug found:** `frontend/src/api/client.js`'s `getAllUsers()` and
  `getRecentEncounters()` threw a generic `HTTP 503` message and
  discarded the backend's actual `detail` field -- unlike `login()` and
  `register()`, which already read `body.detail`. This meant the
  Dashboard and Admin pages showed an unhelpful "HTTP 503" with no way
  to tell what was actually wrong, even though the backend was already
  sending a specific, real error message. FIXED: both functions now
  read and surface `body.detail`, matching the login/register pattern.
  Confirmed `DashboardPage.jsx` already displays `err.message`, so this
  fix surfaces on screen with no further frontend changes needed.

## New feature, Phase 2 of 3: patient-submit -> admin-review -> doctor-attend workflow (backend endpoints)
Builds directly on Phase 1's schema (confirmed working on the user's
real PostgreSQL). Added:

- `persistence.py`: `persist_triage_decision()` now accepts `status` and
  `patient_user_id` -- a patient's repeat submissions now correctly
  reuse THEIR OWN existing patient record (looked up by `user_id`)
  instead of creating a new disconnected one each time (patient
  self-submissions get a fresh random pseudonym each call, so without
  this fix their history would be scattered across separate patient
  rows). New functions: `get_pending_decisions`, `get_available_doctors`,
  `approve_decision`, `reject_decision`, `get_assigned_decisions`,
  `mark_attended`, `get_patient_history` -- all following the exact
  query shapes already proven correct by Phase 1's executed SQLite test
  (pending queue, available-doctors filter, assign, doctor's list,
  attend, status CHECK).
- `main.py`: `/auth/register` now also accepts `'patient'`/`'doctor'`
  roles (same honest self-selection tradeoff already made for `'admin'`
  -- documented in the endpoint's docstring, not hidden). `/triage` now
  accepts `self_submitted`/`submitted_by_user_id`; when true, the
  decision is created as `pending_review` and linked to the patient's
  own account, instead of the existing clinician flow's immediate
  `finalized`. New endpoints: `GET /admin/pending`,
  `GET /admin/doctors/available`, `POST /admin/decisions/{id}/approve`,
  `POST /admin/decisions/{id}/reject`, `GET /doctor/assigned`,
  `POST /doctor/decisions/{id}/attend`, `GET /patient/history`.
- `vite.config.js`: proactively added `/doctor` and `/patient` to the
  dev-mode proxy list -- this is the EXACT bug class found earlier with
  `/admin`/`/health` being missing, caught this time before it could
  bite rather than after.
- **NOTE FOR PHASE 3:** discovered while adding the above -- the
  frontend's page route `/admin` (React Router) already shares its name
  with the backend proxy prefix `/admin`. This is dormant right now
  (client-side nav via React Router doesn't hit the network, so it only
  matters on a hard refresh while on that page, which would incorrectly
  proxy to the backend and 404) but it's a real latent bug, and Phase 3
  MUST NOT repeat it for `/doctor` and `/patient` -- use distinct page
  routes like `/doctor-dashboard` and `/patient-dashboard` instead of
  bare `/doctor` / `/patient` for the new frontend pages.
- **HONEST STATUS:** all new/changed Python files pass `py_compile`;
  the underlying query logic was already proven for real in Phase 1's
  executed SQLite test. This phase's endpoint wiring itself has NOT
  been run against a live server (still no FastAPI/uvicorn installed in
  this sandbox) -- but every new endpoint can be smoke-tested manually
  via the interactive docs at `http://localhost:8000/docs` even before
  Phase 3's frontend exists, which is the suggested next step.
- NEXT: Phase 3 -- the three frontend dashboards (Patient, Doctor, and
  a refactored Admin with the approval/assignment UI), plus the visual
  design pass the user asked for on the Admin dashboard specifically
  (matching the supervisor's reference more closely).

## Restructured the 3 role pages per direct feedback
- **Admin**: kept the redesign, added a dark theme matching the
  MediSys reference -- scoped to just this page (not the whole app)
  via a single `DARK_THEME_VARS` object overriding the shared CSS
  custom properties (`--color-surface`, `--color-border`, `--color-ink`,
  etc.) on a wrapper div. Every child element already referenced these
  same tokens, so this is the only place the palette is defined.
  Caught a real bug while doing this: overriding a CSS custom property
  alone does NOT retroactively change an already-inherited `color`
  value (color is computed once where `color: var(--color-ink)` is
  declared -- at `body` -- and that computed value inherits down
  unchanged). Headings/text would have silently stayed dark-on-dark.
  Fixed by also explicitly re-declaring `color: var(--color-ink)` on
  the wrapper so it re-resolves locally. Chart grid/axis/tooltip
  colors (literal hex, recharts doesn't reliably take CSS vars) updated
  to match.
- **Doctor, renamed "Clinical"** (`ClinicalPage.jsx`, replaces
  `DoctorDashboardPage.jsx`): simplified to a Profile section + patient
  list, no stats/charts (never had any). SCOPE DECISION, explained to
  user rather than silently applied: request was "profile + history of
  attended patients, that's all," which taken literally would remove
  the Mark Attended action -- but that action is the only way a case
  ever becomes "attended," so removing it breaks the very approve ->
  attend loop this feature exists for. Kept it under a small
  "Awaiting You" section above the "Patients I've Attended" history,
  flagged clearly rather than dropped silently.
- **Patient, restructured to "My Profile"** (`PatientDashboardPage.jsx`
  rewritten): one page, three tabs (Profile / New Assessment /
  History) instead of a separate dashboard + separate nav link. "New
  Assessment" tab reuses the existing `IntakePage` component directly
  (already role-aware) rather than duplicating the form.
  `Layout.jsx`'s patient nav collapsed to a single "My Profile" link;
  the standalone "New Assessment" nav item removed (it's a tab now).
  `ResultPage.jsx`'s post-submission notice for patients now deep-links
  into the History tab via router state instead of a plain `<a href>`
  (which would have forced a full page reload).
- **HONEST STATUS:** full syntax sweep (all .py + all .jsx/.js) --
  zero errors. Backend untouched this round, so the schema test wasn't
  re-run. The dark theme's actual visual result (contrast, chart
  legibility) has NOT been seen rendered anywhere -- CSS custom
  property overrides are logically correct but this build environment
  has no browser to screenshot; first real look happens on the user's
  machine.
- NEXT: user to verify all 3 pages live and report back.

## New feature, Phase 2+3: review-workflow frontend, and 4 pages redesigned to match new supervisor references
Continuing the patient-submit -> admin-review -> doctor-attend workflow
(Phase 1 schema was the previous entry). Found the Phase 2 backend
(all review-workflow endpoints) was already fully built from earlier
work in this session; what was missing was the frontend. Built:

- `client.js`: added the 8 missing API functions for the workflow
  (dashboard stats, pending reviews, available doctors, approve,
  reject, assigned decisions, mark attended, patient history).
- `LoginPage.jsx`: now stores `user_id` (not just `role`) in
  localStorage -- needed so the client can say who's submitting/
  approving/attending. Routes each role to its own landing page
  (patient -> `/dashboard/patient`, doctor -> `/dashboard/doctor`,
  admin -> `/admin`, clinician -> `/intake`, unchanged).
- `SignUpPage.jsx`: added Patient and Doctor to the role dropdown.
- `IntakePage.jsx`: submits as a patient self-submission
  (`self_submitted: true`, `submitted_by_user_id`) when the logged-in
  role is 'patient' -- goes to admin review instead of being finalized
  immediately. Added an honest on-screen note for patients on the
  Vitals step: vitals stayed REQUIRED (deliberately did NOT relax this
  to let patients skip or guess vital signs, since that could mask a
  real danger sign on a triage tool) -- the note just asks for a real
  reading, not a "normal" placeholder.
- New `PatientDashboardPage.jsx` ("My Assessments") and
  `DoctorDashboardPage.jsx` ("My Patients"), routed at
  `/dashboard/patient` and `/dashboard/doctor` -- **deliberately NOT**
  `/patient` or `/doctor`, since those prefixes are already claimed by
  the API proxy list in `vite.config.js` and would have silently broken
  on page refresh (the same class of bug as the earlier missing-`/admin`
  proxy issue).
- `Layout.jsx` sidebar nav is now role-aware (4 different nav sets).
- `main.jsx`: registered the two new routes.
- `AdminPage.jsx` fully rebuilt: real stat cards, a real 7-day
  assessments trend line chart, a real diagnosis-breakdown donut chart
  (both via the new `recharts` dependency), quick links, a real recent-
  activity feed (built from actual status transitions, not fabricated
  names), the full pending-review queue with expand/Approve
  (doctor-picker)/Reject actions, and the existing registered-users
  table. New backend: `get_admin_dashboard_stats()` in `persistence.py`
  + `GET /admin/dashboard-stats` in `main.py`.
- `ResultPage.jsx` reworked to match the "MediCore AI" diagnosis-result
  reference: step-progress bar at top (reusing IntakePage's stepper),
  two-column urgency card (description + big tier badge), three summary
  mini-cards. Caught and fixed a real bug during this: first wrote it
  referencing `triage.symptoms_considered`, a field that doesn't exist
  anywhere in the actual backend output (`triage_agent.py`'s real keys
  are only `urgency_classification`, `differential_diagnosis`,
  `red_flag_alerts`, `suggested_care_pathway`) -- would have silently
  always shown "—" instead of real data. Fixed by having `IntakePage`
  pass the actually-submitted symptoms list through navigation state
  instead.
- Design references reorganized: the 4 new supervisor images (admin
  dashboard "MediSys", diagnosis result "MediCore AI", patient history
  "Health History Questionnaire", symptoms "Healthdesk") saved into
  `docs/design_references/`.
- **Scope choice on `patient_history` reference, explained to user, not
  silently deviated from:** that reference is a chronic-disease
  checklist (asthma, diabetes, etc.), which this system's schema has no
  data model for (it tracks per-visit symptoms/vitals/diagnosis, not a
  standing medical history). Built `PatientDashboardPage.jsx` with the
  same clean white-card visual language instead, showing the patient's
  REAL submission history and status.
- **Admin dashboard color choice, explained to user, not silently
  deviated from:** kept this app's own established teal branding
  (used since the login page) rather than switching to the reference's
  unrelated dark-navy "MediSys" identity, which would look inconsistent
  with every other page. Matched the reference's STRUCTURE (stat cards,
  trend + donut charts, quick links, activity feed) closely instead.
- **HONEST TESTING STATUS:** full syntax sweep (py_compile on every .py
  file, esbuild syntax-only check on every .jsx/.js file, including all
  new files) -- zero errors. Re-ran the real executable
  `schema_sqlite_test.py` workflow simulation -- all 6 checks still
  pass. What could NOT be verified here: `recharts` is a brand new
  dependency and has never actually been installed or rendered anywhere
  in this build environment (no npm registry access) -- first real
  test of the charts rendering happens on the user's machine after
  `npm run install:all`. Same for the full click-through of
  patient-submit -> admin-approve-with-doctor-picker -> doctor-attend
  against a real Postgres database -- the SQLite mirror proves the
  query logic works, not that FastAPI/React glue it together
  correctly end-to-end.
- NEXT: user needs to `npm run install:all` again (recharts is new),
  then click through the full loop for real: sign up a patient and a
  doctor account, submit as the patient, approve+assign as admin, mark
  attended as the doctor. Also still open: closer visual pass on
  `symptoms.jfif`/`IntakePage.jsx` if the new "Healthdesk" reference
  diverges from what's already built (not yet compared side-by-side).

## New feature, Phase 1 of 3: patient-submit -> admin-review -> doctor-attend workflow (schema)
User requested a real workflow: patients self-register and submit their
own intake, an admin reviews and approves/rejects (assigning one of the
available doctors), and the assigned doctor sees the case on their own
dashboard and marks it attended. Scoped via 3 clarifying questions
first (self-service patient accounts w/ login; a distinct "doctor" role
separate from clinician/admin; full workflow needed before defense).
Building this in 3 phases, each handed back separately to keep changes
testable -- this entry covers Phase 1 (database).

- `schema_postgres.sql` updated: `users.is_available` (for the Admin
  dashboard's doctor picker, matches the "Available Doctors" idea from
  the supervisor's reference), `patients.user_id` (links a
  self-registered patient's login to their own patient record),
  `triage_decisions.status/assigned_doctor_id/reviewed_by/reviewed_at/
  rejection_reason` (the state machine: pending_review -> approved ->
  attended, or -> rejected; existing clinician-recorded encounters
  default straight to `finalized`, unaffected).
- New `backend/app/db/migration_review_workflow.sql` -- idempotent
  ALTER-based migration so the user's EXISTING live database (with real
  test data already in it) can be upgraded without dropping/losing
  anything. `docs/SETUP.md` updated with the exact command.
- **HONEST STATUS, genuinely stronger than usual for this project:**
  unlike most schema changes so far (syntax-checked only, no live
  Postgres available here), this one was actually EXECUTED and verified
  end-to-end -- `schema_sqlite_test.py`'s new `demo_review_workflow()`
  function was extended to mirror the new columns and really run the
  full state machine (patient submits -> shows in pending queue ->
  admin approves + assigns an available doctor, unavailable doctor
  correctly excluded -> shows on that doctor's assigned list -> marked
  attended -> CHECK constraint correctly rejects an invalid status
  value -> confirmed the existing clinician-intake flow still defaults
  to 'finalized' unaffected). All 6 assertions pass. This is real proof
  the schema design and query logic work, not just that the SQL parses.
  **CONFIRMED on real PostgreSQL:** user ran the migration --
  `ALTER TABLE` x3, `DO`, `CREATE INDEX` x2 all succeeded, sanity check
  showed the existing test decision correctly defaulted to `finalized`
  with data intact. Schema now proven both logically (SQLite harness)
  and for real (user's live Postgres).
- **Real design decision made, not asked about:** the system has no
  real login sessions (frontend only remembers `role` client-side,
  documented in LoginPage.jsx already). Rather than build full
  session/token auth this close to a defense deadline, Phase 2 will
  extend the same existing pattern (client remembers its own user_id
  too, sends it explicitly with requests that need it) -- explicitly
  NOT a real access-control boundary, same honesty caveat already
  established for role storage. Will be flagged in the defense
  prep doc's known-limitations section.
- NEXT: Phase 2 (backend endpoints -- submit as patient, admin
  pending-queue/approve/reject, doctor assigned-list/attend, available-
  doctors list), then Phase 3 (three new frontend dashboards: Patient,
  refactored Admin with approval UI + doctor picker, new Doctor).
- STILL OPEN from earlier: user wants a closer visual match to the
  supervisor's reference images (structure/layout, not just color) --
  agreed to revisit once this workflow's frontend phase is reached, so
  pages aren't redesigned twice.

## New: expandable patient row on the Dashboard
- User asked for a way to click a row and see more detail. Implemented:
  `get_recent_decisions()` now also returns `decision_id`, full
  `differential_diagnosis`, `rationale`, `red_flag_alerts`, and vitals
  (temperature/HR/RR/BP/SpO2) -- previously only a summary row was
  returned. `DashboardPage.jsx` rows are now clickable
  (`ExpandableRow` component); clicking expands an inline panel below
  the row showing the full diagnosis list with probabilities, red
  flags, vitals, symptoms, and the rationale text. No new endpoint
  needed -- one extra round trip avoided by just returning richer data
  from the existing `/encounters/recent` call.
- STILL OPEN, not built yet -- needs scoping first (see conversation):
  a submit -> admin-review/approve -> clinician-attends workflow the
  user described. This is a real architecture decision (new role(s)?
  a status field on triage_decisions? who exactly submits vs reviews
  vs attends?) -- asked the user to clarify before building rather than
  guessing at a multi-day feature this close to a defense deadline.
- STILL OPEN: user says the actual visual design doesn't match the
  supervisor's reference images closely enough. Re-checked
  docs/design_references/NOTES.md -- prior sessions deliberately used
  the references for branding/layout direction (colors, general
  structure) while NOT literally cloning stat categories that don't
  correspond to real data (donut charts, hospital billing/revenue,
  fake activity feeds) -- a documented, principled choice, not an
  oversight. User's supervisor apparently wants a closer visual match
  regardless. Asked user how closely to match (structure/layout parity
  vs current honest-data-only approach) before doing a broader redesign
  pass, since it's real additional work across multiple pages.

## One-command dev setup + real proxy bug fix
User reported the core blocker directly: backend and frontend needed two
separate commands and weren't communicating properly, breaking startup.
Root-caused and fixed:
- **Real bug found:** `frontend/vite.config.js`'s dev-mode proxy list was
  missing `/admin` and `/health`. In two-terminal dev mode, calls to
  `/admin/users` (AdminPage) and `/health` never reached the backend at
  all -- they silently hit the Vite dev server itself, which returned
  its own `index.html` (SPA fallback) instead of JSON, causing
  `res.json()` to fail on unexpected content. This is almost certainly
  what "communication breaching" looked like from the outside. FIXED:
  both paths added to `BACKEND_PATHS`.
- **New: one command runs everything.** Added a root-level
  `package.json` (project root, alongside `backend/` and `frontend/`)
  with `concurrently` as the only new dependency:
  - `npm run dev` -- starts the backend (uvicorn --reload, via the
    venv's own python.exe directly -- avoids relying on
    `venv\Scripts\activate`, which doesn't reliably persist into a
    child process spawned by `concurrently` across
    cmd/PowerShell/bash) AND the frontend (`vite`) together, in one
    terminal, color-labeled BACKEND/FRONTEND. Visit
    http://localhost:5173 -- hot reload, API calls auto-proxied.
  - `npm start` -- builds the frontend once, then runs ONE backend
    process serving both frontend and API on http://localhost:8000
    (the old "single-server" mode from Phase 7, now one command instead
    of five manual steps). Recommended for defense day specifically.
  - `npm run install:all` -- installs frontend node_modules + backend
    pip packages into the existing venv in one go.
  - New `tools/` folder holds the three small Node launcher scripts
    behind these commands (`dev-backend.mjs`, `start-prod.mjs`,
    `install-all.mjs`). Cross-platform (checks for
    `backend/venv/Scripts/python.exe` on Windows or
    `backend/venv/bin/python` elsewhere) though this project is
    Windows-only in practice.
- **New: `backend/.env` support.** Added `python-dotenv` (new
  dependency in `backend/requirements.txt`) and `backend/.env.example`.
  `HANS_DB_PASSWORD` (and optionally `ANTHROPIC_API_KEY`) now load
  automatically at backend startup from `backend/.env` -- fixes the
  exact "forgot to re-set the env var in this terminal" failure mode
  already logged earlier in this file. `.env` was already covered by
  `.gitignore`, so no change needed there.
- `docs/SETUP.md` restructured: new "Quickstart" section at the top
  with the one-time setup + the two daily commands; the old manual
  five/six-step walkthrough kept below, relabeled as a fallback/
  debugging reference, not the primary path anymore.
- **HONEST TESTING STATUS:** this sandbox has no network access, so
  `fastapi`, `uvicorn`, `psycopg2-binary`, `python-dotenv`, and
  `concurrently` cannot actually be installed here, and no live
  PostgreSQL exists here either -- meaning `npm run dev` / `npm start`
  could NOT be run end-to-end in this environment. What WAS actually
  done: (1) every Python file in the project re-verified with
  `py_compile` -- zero errors; (2) every frontend JS/JSX file,
  including the fixed `vite.config.js`, re-verified with `esbuild` in
  syntax-only mode (no bundling/import resolution needed, so this
  works without node_modules installed) -- zero errors; (3) the new
  root `package.json` and `tools/*.mjs` scripts syntax/JSON-validated.
  This is the same honesty pattern as every other "not yet live-tested
  here" entry in this file -- first real run of `npm run dev` happens
  on your machine. Report back exactly what happens.

## Real admin role and Admin page
- Registration now accepts a role (clinician/admin), self-selected at
  signup with an honest on-screen note that there's no approval step in
  this demo build (a real deployment would never allow that).
- New GET /admin/users endpoint (real data: username, role, registration
  date). HONEST SECURITY NOTE stated directly in the code: this endpoint
  has no real access control yet (no session/token system exists), so
  it's only HIDDEN from non-admin users client-side, not actually
  protected server-side. Flagged clearly rather than presented as secure.
- New AdminPage.jsx: shows real registered-user list and role counts.
  Deliberately does NOT show the fake hospital-admin metrics (billing,
  staff, pharmacy) from the reference image -- explicit banner on the
  page itself explains why.
- Admin nav link in the sidebar only appears when the locally-stored role
  (set at login) is 'admin' -- client-side convenience, not a security
  boundary (see note above).
- Full syntax sweep (frontend + backend) -- zero errors. Not yet live-
  tested.
