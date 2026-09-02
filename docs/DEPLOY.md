# Deploying HANS-Triage: GitHub + Render

This deploys the app as ONE Docker container (frontend built and served by
the same FastAPI process you already use for `npm start` locally) plus a
managed Render Postgres database.

## 0. What was added/changed for deployment

- `Dockerfile` (project root) -- builds the frontend with Node, then runs
  it all from a slim Python image with uvicorn. Render builds this
  automatically; you never run Docker locally unless you want to.
- `.dockerignore` -- keeps the image small, keeps `backend/.env` out of it.
- `backend/app/db/connection.py` -- now also accepts a single `DATABASE_URL`
  env var (what Render's managed Postgres gives you), falling back to the
  old `HANS_DB_*` vars for local dev. No other code changed.

## 1. Push to GitHub

```
git init
git add .
git commit -m "Initial commit: HANS-Triage"
git branch -M main
```

Create the empty repo on GitHub (github.com -> New repository -- do NOT
initialize with a README, you already have one), then:

```
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

## 2. Create the Postgres database on Render

1. Render Dashboard -> New -> PostgreSQL.
2. Name it (e.g. `hans-triage-db`), pick the free plan, Create Database.
3. Wait for it to become "Available", then open it and copy the
   **Internal Database URL** (you'll paste this into the web service in
   step 4 -- internal is faster/free since both services live on Render).
   Also copy the **External Database URL** -- you need that one now, from
   your own machine, for step 3.

## 3. Load the schema into it

From your project folder, using the **External Database URL** from step 2:

```
psql "<external-database-url>" -f backend/app/db/schema_postgres.sql
psql "<external-database-url>" -f backend/app/db/migration_review_workflow.sql
```

(No `psql` installed? Render's DB page has a "Connect" -> "PSQL Command"
button that gives you a ready-to-paste command, or you can run these two
files from Render's web Shell once the DB exists.)

## 4. Create the web service

1. Render Dashboard -> New -> Web Service -> connect your GitHub repo.
2. Runtime: **Docker** (Render auto-detects the `Dockerfile`).
3. Instance type: free is fine to start.
4. Environment tab -- add:
   - `DATABASE_URL` = the **Internal Database URL** from step 2
   - `ANTHROPIC_API_KEY` = (optional -- only if you want the Chat Agent to
     make real calls instead of returning its stub response)
5. Create Web Service. Watch the Logs tab -- first build takes a few
   minutes (npm install + vite build + pip install).
6. Once live, open the `.onrender.com` URL Render gives you. Register a
   user, log in, confirm the dashboard loads real data.

## 5. Every future update

```
git add .
git commit -m "<what changed>"
git push
```

Render auto-deploys on every push to `main`. No other steps needed.

## 6. Adding email notifications (Brevo)

Added after deployment: password reset emails, and an email to a patient
when their assessment is approved and assigned to a doctor. Uses Brevo's
HTTP API (not SMTP -- Render's free tier blocks outbound SMTP ports).

**a) Run the migration** against your existing database (adds `email`,
`reset_token`, `reset_token_expires` columns to `users`; safe to run more
than once):
```
psql "<your-database-url>" -f backend/app/db/migration_email_notifications.sql
```

**b) Get a Brevo API key**: sign up at brevo.com (free tier: 300
emails/day) -> Settings -> SMTP & API -> generate a new API key. Also
verify a sender email/domain there -- Brevo rejects sends from an
unverified sender.

**c) Add environment variables** on your Web Service (Environment tab,
same place as `DATABASE_URL`):
- `BREVO_API_KEY` = the key from step (b)
- `BREVO_SENDER_EMAIL` = the verified sender address from step (b)
- `BREVO_SENDER_NAME` = display name, e.g. `HANS-Triage` (optional, has a default)
- `APP_BASE_URL` = your real `https://your-app.onrender.com` URL --
  used to build the link inside password reset emails. Without this
  set correctly, the reset link in the email will point to
  `localhost` and won't work for the patient.

Save, let Render redeploy, then test: use "Forgot Password?" on the
login page with a real email you can check, and separately approve a
patient submission as admin (with that patient's account having an
email on file) to test the approval alert.

If `BREVO_API_KEY` is missing, email sending is silently skipped (logged
in the server logs, not sent) -- registration, login, and the approval
workflow itself all keep working either way; only the notification
emails are affected.

## Troubleshooting

- **Build fails at `npm run build`**: check the Logs tab for the actual
  Vite error; almost always a frontend syntax issue, not a Render issue.
- **App loads but login/register 500s**: `DATABASE_URL` is probably
  missing or wrong -- check the Environment tab. Also confirm step 3 was
  actually run (tables must exist).
- **"Frontend not built yet" JSON response instead of the app**: the
  Docker build didn't produce `frontend/dist` -- check the build logs for
  an npm error.
