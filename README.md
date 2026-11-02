# InfraSight

The AI co-pilot for city streets. A citizen photographs a problem in public space; InfraSight turns it into a mapped
danger, a merged case, a red-outlined damage zone, a picture of the street after repair, a detour, a draft traffic
order, the documents of each legal stage, and a message back to the citizen in their own language. Built on Meta's
models: **Muse Spark**, **SAM 3.1** and **Muse Image**, all through the Meta Model API.

## Built during the Meta Global AI Developer Hackathon
Everything in this repository was written during the hackathon (first commit 29 Oct 2026, building period
27 Oct - 4 Nov 2026): the citizen and staff console, the FastAPI backend, the 10 AI functions, the SAM 3.1 damage
outline, the Muse Image repair preview, danger zones, duplicate merging, detours and traffic orders, hotspots and
forecast, citizen updates in 9 languages, and the weekly brief. See [AI-FUNCTIONS.md](AI-FUNCTIONS.md) for every AI
call and [META-MODELS.md](META-MODELS.md) for the models used and their cost.

## Layout
```
frontend/                  static console, no build step
  index.html  css/styles.css
  js/app.js                views, pipeline, charts, login screen (edit here)
  js/mapview.js            YOUR Leaflet map (index.js) adapted: CityMap.init({role, tickets, zones, onPin, onZone})
  js/map.js                danger zone drawing (point / street / area), mini map in the ticket's Danger tab
  js/api.js                backend client: login token + one function per ticket action (no prompts)
  js/config.js             backend address (empty = the same server as the page)
backend/                   FastAPI + SQLAlchemy + SQLite (infrasight.db, created on first start)
  app/db.py                tables: users, tickets, audit_log, zones
  app/auth.py              passwords (scrypt), login tokens (JWT), role checks, signed photo links, AI rate limit
  app/regulations.py       stages, checklists, directory, regulatory notes (single source, served by GET /api/meta)
  app/serializers.py       DB rows -> frontend ticket shape, filtered per user; AI context for a ticket
  app/routers/auth.py      POST /api/auth/login, /api/auth/register (citizens), GET /api/auth/me
  app/routers/tickets.py   state, create (with AI triage), report, stage assist, checklist, advance, photo, zones
  app/routers/stats.py     GET /api/stats (staff)
  app/services/            ai.py (all prompts, Muse Spark calls), geo.py (OpenStreetMap: pin -> address,
                           street shapes), routing.py (detours), vision.py (SAM 3.1 outline), notify.py (citizen
                           updates), images.py, export.py (report HTML with all images), visuals.py (red
                           damage zone, Muse Image repair preview)
  app/routers/insights.py  hotspots + forecast, weekly brief, notifications
  app/seed.py              sample tickets and demo users (SEED_DEMO)
  app/cli.py               create staff accounts, change roles and passwords
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

## Meta models
All three run on Meta's servers through the Meta Model API (`https://api.meta.ai/v1`), with one key from dev.meta.ai
(`META_API_KEY`). Nothing runs on a GPU locally.

| Model | Used for | Setting |
|---|---|---|
| Muse Spark (`muse-spark-1.3` recommended) | triage, reports, stage documents, size estimate, repair check, traffic order, forecast, brief, citizen updates | `MODEL_QUICK` (triage, updates), `MODEL_DEFAULT` (the rest); empty = `muse-spark-1.1` |
| SAM 3.1 (`sam-3.1`) | exact outline of the damage on the photo | none |
| Muse Image (`muse-image-1.0`) | the street after repair, drawn from the citizen photo | `MODEL_IMAGE` |

Without a key, reports are still saved for manual triage. Prices and what the hackathon credit buys:
[META-MODELS.md](META-MODELS.md).

With `SEED_DEMO=true` and `DEMO_PASSWORD` set, an empty database gets 4 sample tickets in Brest and three users:
`citizen`, `tech`, `elected` (password = `DEMO_PASSWORD`). Do not enable this in production. The sample photos
(`backend/app/demo_photos/`) are not real citizen photos: they were generated with Muse Image, then run once through
the real pipeline (SAM 3.1 outline, Muse Image repair preview), so the demo shows every feature without AI calls at
start. Every report needs a photo.

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
Every call sends a system message (role, steps, definitions of type, severity, urgency and owner, output schema) and
a user message with the data inside `<data>` tags, declared untrusted so citizen text cannot steer the model. Legal
statements must cite their source from the regulatory notes in `regulations.py`, or be marked `[verify]`. JSON
answers are validated against `schemas.py`; an invalid answer is retried once with the validation error. Each user
gets `AI_CALLS_PER_HOUR` AI requests (default 30, in memory). If triage fails, the report is still saved for manual
triage. Every AI call is described in [AI-FUNCTIONS.md](AI-FUNCTIONS.md).

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
- **Live AI pipeline.** After "Send report", the citizen watches the three Meta models work, step by step, with
  timings: Muse Spark's triage (title, type, severity, owner), SAM 3.1's outline, then Muse Image's repaired street.
  The photo in the panel changes at each step. SAM 3.1 and Muse Image run in the background on the server; the panel
  polls the ticket until they finish, and each result is saved on a freshly loaded ticket so a duplicate merged
  meanwhile is not overwritten.
- **Damage zone.** Every report with a photo gets the damaged area drawn in red: first from the box Muse Spark gives
  at triage, then from the exact SAM 3.1 outline, computed in the background. "Outline and measure the damage" redoes
  it and has Muse Spark estimate the real size from visible references (kerb, road marking, manhole).
- **Repair preview.** Muse Image draws the citizen's photo as it should look after the repair, from the photo and the
  red-marked copy. Only the damaged area (SAM outlines and the triage box, widened, soft edge) is taken from the
  drawing; the rest stays the real photo, so cars, signs and light never change. Labelled everywhere as an
  illustration, not a photo. Staff can redraw it.
- **Every report is on the map.** A citizen pins the place on the map, or types an address and picks one of the
  OpenStreetMap suggestions (`GET /api/geocode`, near `COMMUNE_NAME`). The server refuses a report without a place
  and stores the address read from the map, not free text.
- **Better outlines.** Triage names the damage it sees ("cracked asphalt", "broken paving slab"); SAM 3.1 tries that
  phrase first, then phrases for the ticket type (at most 3 calls). Outlines covering half the photo are dropped,
  and one that overlaps the triage box is preferred over damage further down the street.
- **Sourced cost estimate.** Muse Spark only lists the work items and quantities (from the measured damage size);
  the server prices them from `backend/app/prices.py`, unit rates taken from public French price schedules (BPU),
  each line with its source link. Work the catalogue does not cover is marked `[verify]`. A commune replaces the
  rates with those of its own works contract. The ticket's estimate follows the report.
- **Live progress for every AI action.** Full report, detour, stage drafts, damage analysis, repair preview, repair
  check, weekly brief and forecast open a panel that shows each real step as the server does it (for example SAM 3.1
  → Muse Spark → red zone → Muse Image), with its result and timing. The console sends a random id in the
  `X-Progress` header and reads `GET /api/progress/{id}` every 0.4 s (`services/progress.py`).
- **Before / after slider.** On the ticket, a handle reveals the citizen's photo or the repaired street (Muse Image
  illustration, or the real after-repair photo once there is one). Mouse, touch and keyboard.
- **Images everywhere.** Photo, damage zone, repair preview and after-repair photo appear on the ticket, the AI
  report, the danger tab, the acceptance stage (before / expected / after), map popups and the downloaded report.
  Muse Spark also receives the red-marked photo for the full report and the repair check.
- **Incident report (PDF).** "Download PDF report" on the AI report tab (staff): an A4 PDF with the InfraSight logo, key
  facts, the four images, damage size, danger, the AI assessment with cited sources, the 7 stages, repair check,
  detour, history and the draft traffic order. Real selectable text, document language and title, a bookmark per
  section (`services/export.py`, ReportLab). Not a fully tagged PDF/UA.
- **Repair check.** At the last stage, staff add an after-repair photo; the AI compares it with the citizen's photo.
- **Detour and traffic order.** For a street danger zone, "Plan a detour" downloads the roads around it (Overpass,
  `OVERPASS_URLS`, tried in order), computes the shortest legal route around the blocked section (one-way streets
  respected), and the AI drafts the mayor's traffic order (arrêté) in French. Takes up to a minute. The commune's name comes from `COMMUNE_NAME` in `.env`; the order
  number, the dates and hours of the closure and the signing date stay `[à compléter]`: only the town hall decides
  them, so the AI does not invent them. Staff can remove a detour (route and draft order) from the Danger tab, or by
  clicking the blue dashed line on the map, and show or hide all detours with the "Detours" button.
- **Hotspots.** Streets with 2+ reports in 12 months (Hotspots page, purple rings on the map); the AI forecast proposes
  preventive actions and a budget.
- **Updates.** Citizens get a short message at each step, written by the AI in the language they chose (Updates page);
  without AI, a plain template. Staff get an AI weekly brief on the dashboard.

## Deployment
- **CI** (`.github/workflows/ci.yml`): installs the backend and smoke-tests login, tickets and stats on a temporary
  database; checks the JavaScript syntax. No AI calls, no key needed.
- **No hosted copy.** Run it from this repository (see Run). The console and the API are served by the same
  backend; to host it, run the backend on a server and open its address.

## To complete
1. PostgreSQL + PostGIS (`DATABASE_URL`), Alembic migrations. Until then, new columns are added at start
   (`db.add_missing_columns`); renames or type changes still need a fresh `infrasight.db`.
2. `GET /api/stats` into the charts; own Nominatim server (or a paid geocoder) for real traffic.
3. Legal review of every figure in `backend/app/regulations.py`.
4. Password reset by email, login attempt limiting; Redis for the rate limit if you run several workers.
5. `due` is a day count set by hand; turn it into a real deadline date.
