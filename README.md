# InfraSight

AI-powered urban healing platform. Citizens photograph broken infrastructure; the system segments (SAM 3.1), diagnoses (Muse Spark) and visually repairs (Muse Image) it, and gives the city a triage-ready dashboard. See [docs/PITCH.md](docs/PITCH.md).

## Repository
```
client/   Front end (vanilla JS modules, Citizen + Municipal modes). Deployed to GitHub Pages in mock mode.
server/   Back end (Python, FastAPI): tickets, three-tier compliance pipeline, AI endpoints.
docs/     Architecture, API contract, how to add features.
```

## Run the client (mock mode, no server needed)
```
cd client && npm start          # or: python3 -m http.server 8000
npm test
```

## Run the server
```
cd server
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example .env         # then export the variables, or set them in your shell
python -m db.seeds.seed --staff-user admin --staff-password CHANGE-ME
uvicorn main:create_app --factory --reload     # http://localhost:8000 (API under /api, docs at /docs)
pytest                                         # 43 tests, incl. the kill-switch guarantee
```

## How the server is organized (three tiers)
| Tier | What it does | Can be switched off? |
|---|---|---|
| 1 Core | Validate photo + location, AI assessment, create ticket | No: it is the product |
| 2 Admin | Department mapping, SLA | `FLAG_TIER2_ADMIN_ENABLED` |
| 3 Regulatory | Jurisdiction, permit checklist, utility alert, SOP drafts | `FLAG_TIER3_COMPLIANCE_ENABLED` (off by default) |

A ticket always exists even if tiers 2 and 3 fail; every fallback is logged. Details: [docs/modular-compliance-architecture.md](docs/modular-compliance-architecture.md).

## Status (honest)
- The AI models are **mocked**; the utility-alert adapter is a **sandbox** (nothing is sent anywhere); the rule files are **illustrative** and need legal review.
- The client is **not yet connected** to the server (next step; see the guide).

## Docs
[Architecture](docs/ARCHITECTURE.md) · [API](docs/API.md) · [Adding features](docs/ADDING_FEATURES.md) · [Compliance architecture](docs/modular-compliance-architecture.md)
