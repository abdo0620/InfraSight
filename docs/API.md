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
