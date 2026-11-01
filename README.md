# InfraSight

```
frontend/                  static console, no build step
  index.html  css/styles.css
  js/app.js                views, pipeline, charts, login screen (edit here)
  js/mapview.js            YOUR Leaflet map (index.js) adapted: CityMap.init({role, tickets, zones, onPin, onZone})
  js/map.js                danger zone drawing (point / street / area), mini map in the ticket's Danger tab
  js/api.js                backend client: login token + one function per ticket action (no prompts)
backend/                   FastAPI + SQLAlchemy + SQLite (infrasight.db, created on first start)
  app/db.py                tables: users, tickets, audit_log, zones
  app/auth.py              passwords (scrypt), login tokens (JWT), role checks, signed photo links, AI rate limit
  app/regulations.py       stages, checklists, directory, regulatory notes (single source, served by GET /api/meta)
  app/serializers.py       DB rows -> frontend ticket shape, filtered per user; AI context for a ticket
  app/routers/auth.py      POST /api/auth/login, /api/auth/register (citizens), GET /api/auth/me
  app/routers/tickets.py   state, create (with AI triage), report, stage assist, checklist, advance, photo, zones
  app/routers/stats.py     GET /api/stats (staff)
  app/services/            ai.py (all prompts, Muse Spark / Claude calls), geo.py (OpenStreetMap: pin -> address,
                           street shapes), routing.py (detours), vision.py (SAM client), notify.py (citizen
                           updates), images.py, export.py (report HTML with the photo)
  app/routers/insights.py  hotspots + forecast, weekly brief, notifications
  app/seed.py              sample tickets and demo users (SEED_DEMO)
  app/cli.py               create staff accounts, change roles and passwords
sam_server/                SAM 3.1 segmentation server (separate machine with a GPU)
```

## Run
Windows: double-click `start.bat`, then open http://localhost:8000. The first run creates `backend/.venv` and
`backend/.env` (with a generated `SECRET_KEY` and `DEMO_PASSWORD=demo1234`). Put your `META_API_KEY` in `backend/.env`
and restart. Other systems:
```
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env              # fill META_API_KEY, SECRET_KEY, DEMO_PASSWORD
uvicorn app.main:app --reload                                        # site: http://localhost:8000, API docs: /docs
```
The backend serves the console too. Opening `frontend/index.html` as a file does not work.

## AI provider
`AI_PROVIDER=meta` uses Muse Spark through the Meta Model API (`https://api.meta.ai/v1`, OpenAI-compatible, key from
dev.meta.ai). `AI_PROVIDER=anthropic` uses Claude. Model names: `MODEL_QUICK` (triage) and `MODEL_DEFAULT` (report,
stage assist); empty means `muse-spark-1.1`. Without a key, reports are still saved for manual triage.

With `SEED_DEMO=true` and `DEMO_PASSWORD` set, an empty database gets the sample tickets and three users:
`citizen`, `tech`, `elected` (password = `DEMO_PASSWORD`). Do not enable this in production.

## Accounts and roles
- Citizens sign up on the sign-in screen. They see full details of their own reports only; other reports appear on
  the map and in the insights without photo, history or AI output.
- Staff accounts are created by an administrator:
  `python -m app.cli create-user jdupont tech "Jean Dupont"` (roles: citizen, tech, elected).
  Also `set-role` and `set-password`.
- Technicians and elected officials run the pipeline. Only an elected official can sign the decision stage.
  Every action is written to the audit log by the server, with the user's name.

## AI
The browser never sends a prompt. Prompts are in `backend/app/services/ai.py`; the endpoints are
`POST /api/tickets` (triage), `POST /api/tickets/{ref}/report` and `POST /api/tickets/{ref}/stages/{i}/assist`.
Invalid JSON answers are retried once. Each user gets `AI_CALLS_PER_HOUR` AI requests (default 30, in memory).
If triage fails, the report is still saved for manual triage.

## Danger zones
The AI gives each zone a `shape`: `point` (small circle: broken streetlight, small pothole at the edge), `street` (the
problem disrupts traffic or passage: the whole street section is drawn, `radius_m` = length affected) or `area` (wide
dashed circle: flooding, gas leak, risk of collapse). The colour follows the danger level, and is red whenever
`blocked_access` is true. Street shapes come from OpenStreetMap (Nominatim, max 1 request per second); missing ones
are fetched again at each start. A map pin's default text is replaced by the real address.

## AI features
- **Duplicate merging.** A new report within `DUPLICATE_RADIUS_M` (80 m) of an open ticket that the AI judges to be the
  same problem is added to that ticket: the citizen follows it, the photo goes in its history, severity can rise.
  Staff see possible duplicates on the ticket overview and can merge by hand (the duplicate is closed).
- **Damage outline and size.** "Outline and measure the damage": SAM 3.1 (`SAM_URL`) outlines the damage on the photo,
  then Muse Spark estimates its real size from visible references. Without SAM, only the AI estimate.
- **Repair check.** At the last stage, staff add an after-repair photo; the AI compares it with the citizen's photo.
- **Detour and traffic order.** For a street danger zone, "Plan a detour" downloads the roads around it (Overpass,
  `OVERPASS_URLS`, tried in order), computes the shortest legal route around the blocked section (one-way streets
  respected), and the AI drafts the mayor's traffic order (arrêté) in French. Takes up to a minute.
- **Hotspots.** Streets with 2+ reports in 12 months (Hotspots page, purple rings on the map); the AI forecast proposes
  preventive actions and a budget.
- **Updates.** Citizens get a short message at each step, written by the AI in the language they chose (Updates page);
  without AI, a plain template. Staff get an AI weekly brief on the dashboard.

## SAM server
On a machine with an NVIDIA GPU: `cd sam_server && pip install -r requirements.txt && uvicorn server:app --host 0.0.0.0
--port 8100`, then `SAM_URL=http://<that machine>:8100` in `backend/.env`. The model (`SAM_MODEL`, default
`facebook/sam3.1`, about 1.7 GB) downloads on first start; accept its licence on huggingface.co and `hf auth login`
if asked. CPU works but takes tens of seconds per photo.

## To complete
1. PostgreSQL + PostGIS (`DATABASE_URL`), Alembic migrations. Until then, new columns are added at start
   (`db.add_missing_columns`); renames or type changes still need a fresh `infrasight.db`.
2. `GET /api/stats` into the charts; own Nominatim server (or a paid geocoder) for real traffic.
3. Legal review of every figure in `backend/app/regulations.py`.
4. Password reset by email, login attempt limiting; Redis for the rate limit if you run several workers.
5. `due` is a day count set by hand; turn it into a real deadline date.
