# Modular & Gradual Compliance: implementation guide

This is the **implementation** of the target design. The core rule:

> The core app must work even if every administrative and regulatory feature is disabled, misconfigured, or failing.

## Tiers and where they live

| Tier | Folder (server) | Flag | If it fails |
|---|---|---|---|
| 1 Core (mandatory) | `services/core/`, `routes/reports.py`, `routes/tickets.py` | none | Bad upload is rejected before a ticket exists; a model failure becomes `uncategorized` / `unknown` + human review. |
| 2 Basic admin | `services/admin/`, `routes/admin.py` | `FLAG_TIER2_ADMIN_ENABLED` (on) | Default SLA, department left unassigned, ticket goes to the unclassified queue. |
| 3 Regulatory | `services/compliance/`, `adapters/`, `routes/compliance.py` | `FLAG_TIER3_COMPLIANCE_ENABLED` (off) + sub-flags | Queue or degrade; ticket continues. Routes return `501` when off. |

`services/workflow/pipeline.py` is the only place that knows about all tiers. It runs **after** the response, step by step, with bounded retries; every failure or skip is written to `ticket_fallbacks` and `ticket_events`.

## Compliance level (stored on `tickets.compliance_level`)
- **1 CORE**: ticket exists.
- **2 STANDARDIZED**: tier-2 steps ran (a failed department mapping still leaves the default SLA).
- **3 REGULATED**: jurisdiction resolved and tier-3 steps ran. If a later step failed, `ticket_compliance.status = 'degraded'` and the admin API shows `3-DEGRADED`.
- If the jurisdiction lookup fails, nothing further in tier 3 can apply: the ticket stays at its previous level and lands in the queue.
- The level never goes down on reprocessing.

## Rules enforced by tests
- `tests/core/test_kill_switch.py`: tier 1 works with every flag off and every adapter dead (and with flags on but everything failing).
- `tests/test_import_rules.py`: `services/core` cannot import admin / compliance / workflow / adapters; `services/admin` cannot import compliance / workflow / adapters.

## Where data and rules live
- Reference data is **data, not code**: `server/compliance-rules/` (jurisdictions, permit checklists, SLA policies) and `server/db/seeds/departments.json`. They are seeded idempotently at startup.
- **The rule files are illustrative.** Their regulatory values come from the architecture document and must be verified by the municipality's legal team before real use.

## Differences from the design document (on purpose)
| Design | Here | Why |
|---|---|---|
| PostgreSQL + PostGIS, `GEOGRAPHY` columns | SQLAlchemy models on SQLite for development; `lat`/`lng` floats; jurisdiction matching by bounding box | Runs anywhere with zero setup. Switch `DATABASE_URL` to PostgreSQL later; PostGIS geometry is the next step. |
| `config/feature-flags.ts` | `server/config/feature_flags.py` | Backend is Python. |
| `jurisdictions.geometry` | `jurisdictions.code` + `config.bbox` | See above. |
| `tickets` has no extra columns | adds `needs_human_review` | The doc requires the flag; a column is simpler than an event lookup. |
| SLA computed "at assignment time" | anchored to the ticket's creation time | Stable on reprocessing and fairer to the citizen. |
| Utility alert to 811 / DT-DICT | **sandbox adapter returns a simulated receipt** (`SIM-...`) | Nothing is sent to any real operator. Implement the real provider in `adapters/utilities/`. |
| Muse Spark / SAM / Muse Image | mock clients in `services/ai/` (`AI_MOCK=1`); with `AI_MOCK=0` the endpoints return `501` | The real model access is not wired yet. |
| `routes/projects`, `routes/signoffs`, renovation-project entities | not built | The renovation-workflow spec was not part of this change. Client placeholder pages exist (`projects`, `inspections`, `notices`). |
| Auth | HMAC-signed tokens, staff accounts in the `users` table (`python -m db.seeds.seed --staff-user NAME --staff-password PW`); citizens report anonymously | Minimal and standard-library only. Replace with your identity provider before production. |

## Not done yet
- The **client is not wired to the server**: it still runs on the browser mock and local storage, which is also what the GitHub Pages deploy serves. Next step: replace `client/src/services/storage/caseStore.js` and `services/ai/remote.js` with calls to `/api`.
- Database migrations (Alembic): tables are created with `create_all` on startup.
- Server-side PDF generation (the client still builds PDFs).
- Real adapters (jurisdiction, zoning, utilities, permits) and real model clients.
