# Backend API contract (used when `AI.useMock = false`)

All endpoints are `POST`, return JSON, and take `multipart/form-data`. API keys stay on the server.

| Endpoint | Request fields | Response |
|---|---|---|
| `/api/segment` | `image` (JPEG), `point` (JSON `{"x":0..1,"y":0..1}`) | `{ "mask": "data:image/png;base64,..." }` transparent except the damage |
| `/api/assess` | `image` (JPEG), `mask` (PNG) | see below |
| `/api/repair` | `image` (JPEG), `mask` (PNG) | `{ "image": "data:image/jpeg;base64,..." }` |

`/api/assess` response:
```json
{
  "damage_type": "Road surface damage",
  "severity": 6,
  "tripping_hazard": "Moderate",
  "exposed_materials": ["Gravel base"],
  "accessibility_impact": "Blocks wheelchair and stroller passage",
  "recommended_action": "Schedule patch repair within 2 weeks",
  "priority": "Standard"
}
```
`severity` is 1-10. `priority` is `Low`, `Standard` or `Urgent`.

Models: SAM 3.1 (segment), Muse Spark (assess), Muse Image (repair). Wire them in your backend following each provider's documentation.

---

# Ticket API (server v0.2)

Run: `cd server && uvicorn main:create_app --factory --reload` (serves the API under `/api` and the client at `/`).
Tier = which part of the [modular compliance architecture](modular-compliance-architecture.md) the endpoint belongs to.

| Endpoint | Tier | Auth | Notes |
|---|---|---|---|
| `POST /api/reports` | 1 | none | multipart: `image`, `lat`, `lng`, `description`. Returns `public_ref` immediately; enrichment runs after the response. `422 {detail:{code,message}}` for invalid image/location. A repeat of the same photo within 24h returns the existing ticket (`duplicate: true`). |
| `GET /api/tickets/{ref}` | 1 | none | Citizen view: status, category, severity, `sla_due_at` if known. |
| `GET /api/tickets/{ref}/events` | 1 | none | Public timeline (`created`, `status_change`). |
| `POST /api/auth/login` | - | none | `{username,password}` -> `{token,role}`. Send `Authorization: Bearer <token>`. |
| `GET /api/admin/tickets` | 2 | staff | All tickets, most severe first, with `compliance_label` (`1`, `2`, `3`, `3-DEGRADED`). |
| `PATCH /api/admin/tickets/{id}` | 2 | staff | `{category?, department_id?, status?}`. Invalid status transition -> `409`. |
| `GET /api/admin/queue/unclassified` | 2 | staff | Worklist of tickets where an enrichment fell back. |
| `POST /api/admin/tickets/{id}/reprocess` | 2 | staff | Re-run enrichment (idempotent). |
| `GET /api/admin/flags` | 2 | staff | Current feature flags. |
| `GET /api/compliance/tickets/{id}` | 3 | staff | Jurisdiction, permits, utility alerts, SOP drafts, fallbacks. |
| `POST /api/compliance/tickets/{id}/permits` | 3 | staff | Create/refresh the permit checklist. |
| `POST /api/compliance/tickets/{id}/utility-alert` | 3 | staff | Submit the Call-Before-You-Dig / DT-DICT alert. |
| `POST /api/compliance/tickets/{id}/sop` | 3 | staff | Generate SOP + traffic plan drafts. |
| `POST /api/compliance/sop/{doc_id}/approve` | 3 | staff | Human approval (drafts start unapproved). |

All `/api/compliance/*` routes return **`501`** while `FLAG_TIER3_COMPLIANCE_ENABLED` is off.
