# SETUP.md — Things YOU need to run locally

This file tracks every command you need to run on your own machine (in VS Code's
terminal) because Claude's build environment has no internet access.
Run these in order, only when this file tells you to — I'll update it as we go.

## Quickstart — one command to run everything

This is the fix for the "two commands, backend and frontend not talking to
each other" problem. Do the one-time setup below once; after that, every
future session is just `npm run dev`.

**One-time setup** (only needed once, or after pulling new dependencies):
1. Everything in "PHASE 0" and "PHASE 3, step 1" below first — Python 3.11,
   Docker, and the backend venv all need to exist before this works.
2. From the project ROOT folder (not `backend/`, not `frontend/`):
   ```
   npm run install:all
   ```
   This installs the frontend's node_modules AND the backend's pip
   packages (into the venv you already created) in one go. **Run this
   again any time you get an updated zip that added a new dependency**
   (e.g. `recharts`, added for the Admin dashboard's charts) — a new
   line in `package.json`/`requirements.txt` alone doesn't install
   itself, this command does.
3. Copy `backend/.env.example` to `backend/.env` and set your real
   Postgres password in it (see PHASE 4 below for Postgres install/setup
   if you haven't done that part yet). This file is read automatically
   every time the backend starts — you will never need to run
   `$env:HANS_DB_PASSWORD = "..."` by hand again.
4. If you want the Chat Agent to make real Claude API calls, also add
   `ANTHROPIC_API_KEY=...` to that same `backend/.env` file (optional —
   everything else works fine without it).

**Every day after that, from the project ROOT folder:**
```
npm run dev
```
This starts BOTH servers together, in one terminal, labeled `BACKEND` /
`FRONTEND` in different colors. Open **http://localhost:5173** — that's
the real app, hot-reloading on every frontend save, automatically
proxying every API call to the backend on port 8000. Ctrl+C once stops
both.

**Before defense day (or anytime you want ONE port instead of two):**
```
npm start
```
This builds the frontend once and serves the whole app — frontend AND
API — from a single process on **http://localhost:8000**. No hot reload
(re-run it after any frontend change), but fewer moving parts to explain
in the room.

Everything below this point is the detailed, phase-by-phase reference —
useful if something above fails and you need to debug a specific piece,
but you shouldn't need to run these commands by hand day-to-day anymore.

## Status: Phase 0 — Environment Setup

Your check: Python 3.14.5 ✅ | Git 2.55.0 ✅ | Docker ❌ missing

### 1. Install Docker Desktop (Windows)
1. Download from https://www.docker.com/products/docker-desktop/
2. During install, make sure "Use WSL 2 instead of Hyper-V" is checked
3. If it asks you to install WSL2 first and fails, open PowerShell **as
   Administrator** and run:
   ```
   wsl --install
   ```
   Then restart your PC, and re-run the Docker Desktop installer.
4. After install, open Docker Desktop once (it needs to run at least once
   to finish setup), then confirm in a fresh terminal:
   ```
   docker --version
   ```

## Status: Phases 3 & 4 — Running the backend + databases locally

Neither of these has been run on a live system yet — you'll be doing both
for the first time. Do them in order (backend first, then databases),
since the database steps assume the venv from step 1 already exists.

### PHASE 3 — Backend server

**1. Install backend dependencies**
Open a terminal in the RazaqFYP folder, using your Python 3.11 install:
```
cd backend
C:\Users\USER\AppData\Local\Programs\Python\Python311\python.exe -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
(After `venv\Scripts\activate`, your prompt should show `(venv)` at the
start — that means it worked and you're using the project's isolated
Python environment, not your system one.)

**2. Run the server**
```
cd app
uvicorn main:app --reload --port 8000
```
Then open http://localhost:8000/docs in your browser — this gives you an
interactive page to test the /triage endpoint directly, no frontend needed
yet.

**3. (Optional) Chat Agent — set your own Anthropic API key**
The Chat Agent is a stub until you set this:
```
set ANTHROPIC_API_KEY=your-key-here
```
(Run this in the same terminal, before starting uvicorn. Without it, the
Chat Agent will return a clearly-labeled stub response — everything else
works fine either way.)

### PHASE 4 — Databases

Good news: I noticed in an earlier screenshot you already have
`postgresql-18.4-2-windows-x64` sitting in your Downloads folder — no need
to download it again.

**1. Install PostgreSQL**
1. Run the installer you already have. Set a password for the `postgres`
   superuser when prompted — write it down, you'll need it.
2. Keep the default port (5432).
3. After install, open "SQL Shell (psql)" from the Start menu, connect with
   the password you set, then create our database:
   ```sql
   CREATE DATABASE hans_triage;
   \c hans_triage
   ```
4. Run our schema against it:
   ```
   psql -U postgres -d hans_triage -f backend/app/db/schema_postgres.sql
   ```
5. **Important for audit log immutability (Module 4.4):** once the schema
   is loaded, run this to enforce append-only at the database level too
   (defense-in-depth, on top of the application code already doing this):
   ```sql
   REVOKE UPDATE, DELETE ON audit_log FROM postgres;
   -- (in production, do this for whatever role your app actually
   -- connects as, not the postgres superuser -- we'll create a proper
   -- app-specific role in a later phase)
   ```

**2. Install MongoDB (Community Server)**
1. Download from https://www.mongodb.com/try/download/community
2. Default settings are fine during install; it'll install as a Windows
   service and start automatically.
3. Confirm it's running:
   ```
   mongosh
   ```
   If it connects and shows a prompt, it's working. Type `exit` to leave.

**3. Add DB driver packages to the project**
```
cd backend
venv\Scripts\activate
pip install psycopg2-binary pymongo
```

**3. Upgrading an existing database (you already have one)**

If you already ran the schema once and have real test data in it (you
do), don't re-run `schema_postgres.sql` — it will error on tables that
already exist. Instead, run the migration that adds the new
patient-submit / admin-review / doctor-attend columns without touching
your existing data:
```
psql -U postgres -d hans_triage -f backend/app/db/migration_review_workflow.sql
```
The last line it prints is a sanity check showing every decision_id in
your database and its status — your existing test assessment should
show `finalized`.

### PHASE 6 — HL7/FHIR round-trip test

This one's a good sign if it works AND if it fails -- it hits a real
public internet server, so a failure might just mean that server is
temporarily down (it has documented uptime issues), not that our code is
wrong.

```
venv\Scripts\activate
pip install -r backend\requirements.txt
python scripts\test_fhir_roundtrip.py
```

Expected output: a series of `HTTP 200`/`HTTP 201` lines, ending with
`PASS: FHIR round-trip test`. If you get a network error instead, try
again in a few minutes (public server may be temporarily down) -- if it
keeps failing, paste the exact error.

### PHASE 7+ — Running as ONE server (frontend + backend + database)

**SUPERSEDED by the Quickstart at the top of this file** (`npm run dev`
for daily use, `npm start` for single-port mode). The steps below are
kept only as a manual fallback/debugging reference — useful if the
one-command scripts ever fail and you want to see exactly what they do
under the hood, or if you need to run a piece by hand to isolate a
problem.

**1. Install the new backend dependency (psycopg2, for database access):**
```
cd backend
venv\Scripts\activate
pip install -r requirements.txt --timeout 120
```

**2. Set your database password.** If you've done the Quickstart setup
(copied `backend/.env.example` to `backend/.env`), this is already
handled automatically and you can skip to step 3. Otherwise, for manual
runs only:
```
$env:HANS_DB_PASSWORD = "your-postgres-password-here"
```
This only lasts for the current terminal session -- you'll need to set it
again in any new terminal window, including if you restart the server
later. (This exact friction is why `backend/.env` was added.)

**3. Seed a real demo user** (same terminal, password still set):
```
cd ..
python scripts\seed_demo_user.py
```
Expected: a confirmation printing username `nurse_amina` and a password.
This is now the ONLY login that will actually work -- login checks real
credentials now, not placeholder text.

**4. Build the frontend once:**
```
cd frontend
npm install
npm run build
```
This creates `frontend/dist/` -- static files FastAPI will serve
directly. You only need to re-run `npm run build` after changing
frontend code, not every time you start the app.

**5. Start the server (this now serves EVERYTHING -- frontend, API, all of it):**
```
cd ..\backend
venv\Scripts\activate
$env:HANS_DB_PASSWORD = "your-postgres-password-here"
cd app
uvicorn main:app --reload --port 8000
```

**6. Open your browser to `http://localhost:8000`** (not 5173 -- that was
only ever the separate frontend dev server's port, not needed anymore for
normal use). You should see the login page.

**7. Log in for real** with `nurse_amina` / `TriageDemo2026!` (also shown
on the login page itself). Try a wrong password too -- it should now
genuinely fail with an error message, proving credential checking is real.

**8. Run a triage assessment**, then check the **Dashboard** link in the
sidebar -- it should show that real assessment, pulled live from
PostgreSQL.

If the Dashboard shows a database error, double-check HANS_DB_PASSWORD is
set in the terminal currently running uvicorn specifically (not just the
one you ran the seed script in) -- it's easy to forget it doesn't carry
over between terminal windows.

**Optional -- Two terminals with hot-reload (only if actively editing frontend code):**
If you're making frequent frontend changes and want instant reload
without re-running `npm run build` every time:
```
cd frontend
npm run dev
```
Then use `http://localhost:5173` instead -- it proxies API calls to your
backend automatically (vite.config.js). Make sure the backend from step 5
above is also running. Switch back to the one-server way (rebuild +
localhost:8000) once you're done editing, especially before defense day
-- fewer moving parts to explain or go wrong in the room.

Report back with any errors from any of these steps.
