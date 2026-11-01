# How the AI works in InfraSight

All AI code is in [backend/app/services/ai.py](backend/app/services/ai.py). The browser never talks to the AI: a button
calls an endpoint on the backend, and the endpoint calls one of the functions below.

## Common mechanics

- **One model provider.** Every function goes through `_ask()`, which calls the Meta Model API (`_ask_meta`,
  OpenAI-compatible) with `META_API_KEY` from `backend/.env`.
- **Two model tiers.**
  - `quick` (`MODEL_QUICK`): fast and cheap jobs (triage, citizen messages).
  - `default` (`MODEL_DEFAULT`): heavier jobs (reports, documents).
  - Both are set to `muse-spark-1.3` in `backend/.env`. Without those lines, the code falls back to
    `muse-spark-1.1`.
- **How every prompt is built.** Each call sends two messages:
  - a **system message**: the role, the steps to follow, the definitions (type, severity, urgency, owner, danger
    zone) and the exact output format;
  - a **user message**: the data only, each piece inside `<data name="…">` tags.

  The system message says that anything inside `<data>` is untrusted and must never be followed as an instruction,
  so a citizen can't steer the AI from the description field.
- **Shared rules** (top of [ai.py](backend/app/services/ai.py)), reused by the prompts that need them:
  - `GROUNDING`: use only the facts given, and write "not stated" instead of guessing;
  - `SOURCING`: every legal statement ends with its source, copied from the regulatory notes, e.g.
    "(art. L2213-1 CGCT)", or with `[verify]` if the notes don't support it. Never cite an article that isn't there.
  - `TYPES`, `SEVERITY`, `URGENCY`, `OWNERS`, `ZONE_RULES`: the definitions of each scale and category.
- **Regulatory notes** (`REG` in [regulations.py](backend/app/regulations.py)): one rule per line, each ending with
  its source. Lines with no known source say "(source not stated [verify])", so the AI flags them.
- **JSON answers are checked.** Six functions need structured data, so they go through `_ask_model()`:
  1. it asks for JSON following a written schema;
  2. it checks the answer against a schema in [schemas.py](backend/app/schemas.py);
  3. if the answer is invalid, it retries once and tells the model exactly what was wrong.

  If both attempts fail, the user sees "The AI answer could not be read".
- **Quota.** Every call started by a button counts toward **30 AI calls per user per hour** (`ai_quota` in
  [auth.py](backend/app/auth.py)). Background citizen messages don't count.
- **Traceability.** What the AI writes into a ticket's history is tagged "AI-generated, human review required".
- **No key, no crash.**
  - A citizen report is still saved, for manual triage.
  - Background messages fall back to a plain fixed text.
  - The buttons show an error.

## The 10 functions at a glance

| # | Function | Tier | Who | Page | Trigger |
|---|---|---|---|---|---|
| 1 | `triage` | quick | Citizen | Report a problem / Map | Send report |
| 2 | `full_report` | default | Staff | Ticket → AI report tab | Generate full report |
| 3 | `stage_assist` | default | Staff | Ticket → Pipeline tab | AI assist for this stage |
| 4 | `estimate_size` | default | Staff | Ticket → Overview tab | Outline and measure the damage |
| 5 | `check_repair` | default | Staff | Ticket → Pipeline tab, last stage | Check the repair with AI |
| 6 | `traffic_order` | default | Staff | Ticket → Danger and zone tab | Calculate the detour |
| 7 | `forecast` | default | Staff | Hotspots | Make a forecast |
| 8 | `weekly_brief` | default | Staff | Dashboard | Write this week's brief |
| 9 | `citizen_update` | quick | Citizen (receives it) | Updates | Automatic, in the background |
| 10 | `repair_preview` | Muse Image | Citizen and staff (see it) | Every ticket view, map popup, report | Automatic after a report; Outline and measure; Draw the repair preview again |

"Staff" means a technician or an elected official.

## Each function in detail

### 1. `triage`: first reading of a citizen report

- **Page:** "Report a problem", or a click on the Map (citizen).
- **Endpoint:** `POST /api/tickets` ([tickets.py](backend/app/routers/tickets.py), `create`).
- **Sends:** the photo, the address, the description, and the 20 nearest open tickets with their distance.
- **Gets back:**
  - a title, a type, and severity and urgency (1–5);
  - the land owner;
  - the consequences if nothing is done;
  - a danger zone (point, street or area);
  - possibly `duplicate_of`.
- **Effect:**
  - Creates the ticket and fills its fields.
  - If `duplicate_of` names an open ticket within 80 m, the report is **merged** into that ticket instead, and the
    citizen becomes a follower of it.
  - The danger zone is then shaped along the real street by [geo.py](backend/app/services/geo.py).

### 2. `full_report`: complete analysis of a ticket

- **Page:** a ticket's **AI report** tab (staff).
- **Endpoint:** `POST /api/tickets/{ref}/report`.
- **Sends:**
  - the photo and the full ticket context (`ticket_ctx` in [serializers.py](backend/app/serializers.py));
  - the legal notes `REG` and the directory of authorities from [regulations.py](backend/app/regulations.py).
- **Gets back:**
  - severity with its reason, urgency, response time;
  - the responsible authority, and an ownership assessment;
  - the rules: procurement, authorizations, council vote, legal notes;
  - a cost range, risks, an action list;
  - a message to the citizen;
  - consequences and danger zone.
- **Effect:**
  - Saved on the ticket and shown in the tab.
  - "Apply severity N to ticket" copies its severity onto the ticket (a human decides).
  - "Download report with photo" exports it.

### 3. `stage_assist`: drafts for each repair stage

- **Page:** a ticket's **Pipeline** tab, current stage only (staff).
- **Endpoint:** `POST /api/tickets/{ref}/stages/{n}/assist`.
- **Sends:** the photo, the ticket context, `REG`, and the task text of that stage (`"p"` in `STAGES`,
  [regulations.py](backend/app/regulations.py)).
- **Gets back:** plain text under 230 words, shown under the stage. It has one numbered section per deliverable, each
  with a heading in capitals (e.g. "1. INSPECTION CHECKLIST"). Values staff must supply are marked `[to fill]`.
  The deliverables depend on the stage:

| Stage | What the AI drafts |
|---|---|
| 1. Intake and registration | Check of type and severity, missing information, duplicates, acknowledgement to the citizen |
| 2. Technical and financial study | Inspection checklist, ownership checks, cost range, who to inform |
| 3. Arbitration and decision | Decision memo, purchase order or council deliberation, legal basis |
| 4. Public procurement | Outline of the technical specification (CCTP), procurement mode for the amount, documents, criteria |
| 5. Authorizations | Network operator declarations (DT-DICT), draft traffic order, signage and information plan |
| 6. Execution and monitoring | Service order, inspection checkpoints, safety checks, photo list |
| 7. Acceptance and closure | Acceptance checklist (OPR), acceptance report, payment steps, closing message |

### 4. `estimate_size`: real size of the damage

- **Page:** a ticket's **Overview** tab, "Photo and description" panel (staff).
- **Endpoint:** `POST /api/tickets/{ref}/damage`.
- **Before the AI:** SAM 3.1 outlines the damage on the photo first ([vision.py](backend/app/services/vision.py)). It
  runs on the Meta Model API (`sam-3.1`, $0.0025 per image), or on your own SAM server if `SAM_URL` is set. If SAM
  fails, the AI still measures the damage and gives its own box.
- **Sends:** the photo, the damage type, and the SAM outline boxes when available.
- **Gets back:** width, length, depth, area, which known references were used (kerb, manhole, road marking…), and a
  confidence level.
- **Effect:** shown on the ticket, with the red SAM outline over the photo.

### 5. `check_repair`: was it really fixed?

- **Page:** a ticket's **Pipeline** tab, last stage (Acceptance) (staff).
- **Endpoint:** `POST /api/tickets/{ref}/after-photo`.
- **Sends:** the citizen's photo (if any), the after-repair photo, and a summary of the ticket.
- **Gets back:** a verdict (repaired / partial / not repaired / unclear), an explanation, and remaining issues.
- **Effect:** saved on the ticket and written to its history.

### 6. `traffic_order`: the mayor's road-closure order

- **Page:** a ticket's **Danger and zone** tab (staff). Only available when the danger zone is a **street**.
- **Endpoint:** `POST /api/tickets/{ref}/detour`.
- **Before the AI:** the detour is computed **without AI** by [routing.py](backend/app/services/routing.py), from the
  OpenStreetMap road network.
- **Sends:** the ticket summary, the street name, the closed length, and the detour streets in order.
- **Gets back:** a draft *arrêté municipal* (traffic order), **in French**, in the standard structure (title, *Vu*,
  *Considérant*, 7 articles, signature). Missing values are marked `[à compléter]` and points to check
  `[à vérifier]`.
- **Effect:**
  - The detour is drawn in blue on the maps.
  - The order is saved on the ticket for the mayor to check and sign.

### 7. `forecast`: where problems will come next

- **Page:** **Hotspots** (staff).
- **Endpoint:** `POST /api/hotspots/forecast` ([insights.py](backend/app/routers/insights.py)).
- **Sends:** the top 10 streets with repeated reports over 12 months (count, types, severity, cost, dates), and the
  current month.
- **Gets back:**
  - a summary;
  - for each street: risk, expected problem, reason, preventive action, budget in euros.
- **Effect:**
  - Saved; the latest forecast reappears on the page.
  - The hotspot streets are drawn as purple rings on the map.

### 8. `weekly_brief`: summary for elected officials

- **Page:** **Dashboard**, top of the page (staff).
- **Endpoint:** `POST /api/brief`.
- **Sends:** facts computed from the database by `week_facts` (no AI in that part):
  - new reports, by type;
  - tickets closed this week, total still open;
  - open high-severity tickets, blocked streets, overdue tickets;
  - tickets awaiting an elected signature;
  - committed budget, merged duplicates, top hotspots.
- **Gets back:** text under 250 words, in English, in five sections:
  - Headlines;
  - Safety;
  - Decisions waiting for you;
  - Money;
  - Trends.

  The AI is told to use only these facts.
- **Effect:** saved; the latest brief stays on the Dashboard.

### 9. `citizen_update`: messages to the citizen

- **Page:** the citizen's **Updates** page.
- **When:** automatically, after the response is sent ([notify.py](backend/app/services/notify.py)):
  - report received;
  - report merged into an existing case;
  - each completed stage;
  - case closed.
- **Sends:** the language the citizen chose, the ticket's reference, title, address and description, what happened,
  and the next step.
- **Gets back:** a friendly message under 60 words in the citizen's language, with no jargon, no invented dates and no
  promises.
- **Fallback:** if there is no key or the AI fails, a plain fixed message is sent instead.

### 10. `repair_preview`: the street after repair (Muse Image)

- **Model:** Muse Image (`muse-image-1.0`, or `MODEL_IMAGE` in `.env`), through `POST /v1/images/edits` on the same
  Meta Model API and key. About $0.01 per image.
- **When:**
  - automatically in the background after a citizen report with a photo
    ([visuals.py](backend/app/services/visuals.py), `preview_later`);
  - again with "Outline and measure the damage";
  - with "Draw the repair preview again" (staff, `POST /api/tickets/{ref}/preview`).
- **Sends:** the citizen photo, and the same photo with the damage in red. The API has no mask parameter, so the red
  copy tells the model which part to repair. It also sends the ticket type and description.
- **Gets back:** the photo with only the damage repaired. It is converted to a 1280 px JPEG and stored in `uploads/`.
- **Shown:**
  - in the image gallery on the ticket (Overview, AI report), labelled "Illustration, not a photo";
  - in the Acceptance stage as "Expected", next to the real after-repair photo;
  - in the downloaded report.

### The red damage zone (not an AI call itself)

[visuals.py](backend/app/services/visuals.py) draws the damaged area in translucent red on the citizen photo, with
Pillow. Where the area comes from:

1. **SAM 3.1** outline (precise). It runs on the Meta Model API: model `sam-3.1` on `POST /v1/responses`, read
   with Meta's `meta-sam-parser`, so no GPU is needed. It runs:
   - in the background after every citizen report, before the repair preview;
   - again with "Outline and measure the damage".

   It uses your own SAM server instead if `SAM_URL` is set.
2. Until SAM has answered, or if it fails, a **box from Muse Spark**:
   - `damage_box` in `triage`, so every report with a photo gets a red zone at once;
   - `box` in `estimate_size`, when the damage is analysed again.

   It is drawn as an ellipse a little wider than the box, and labelled "approximate".

**Used by:**
- **The AI:**
  - `full_report` gets it as a second image, so it knows where the damage is;
  - `check_repair` compares the after photo with it;
  - `repair_preview` uses it to know what to repair.
- **The interface:**
  - the ticket gallery;
  - the Danger and zone tab;
  - the map popup;
  - the "Before" image in the Acceptance stage;
  - the downloaded report.

`configured()` is not an AI call: it only checks whether `META_API_KEY` is set.

## Points to analyse

- **Repair preview is an illustration.** The image model may change more than the damaged area (the API has no mask),
  or show a repair nicer than the real one. It's labelled everywhere as "not a photo", but it should never be used as
  proof of anything.
- **The AI box is approximate.** If SAM finds nothing (for example when the word it gets, like "pothole", doesn't
  match the damage), the red zone depends on Muse Spark locating the damage in the photo. Check a few real reports.
- **SAM's word comes from the ticket type** (`PROMPTS` in [vision.py](backend/app/services/vision.py)): "Other"
  becomes "damage", which SAM may not recognise.

- **Triage is the most sensitive call.** It runs on every citizen report, and it's the only one that changes data
  without a human clicking:
  - it creates the ticket;
  - it can merge a report into another ticket.

  A wrong `duplicate_of` merges two different problems. Only the 80 m distance check guards against it.
- **Three severity values exist:**
  - the one from triage;
  - the one from the full report;
  - the one a human applies.

  The interface prefers the report's version when there is one. Check whether they can disagree without anyone
  noticing.
- **Mixed languages:**
  - `traffic_order` is in French;
  - `weekly_brief` is in English;
  - `citizen_update` is in the citizen's language;
  - everything else is in English.
- **Legal content:** `full_report`, `stage_assist` and `traffic_order` depend on `REG` in
  [regulations.py](backend/app/regulations.py). The AI cites the source of each legal point and marks unsupported
  ones with `[verify]`, but the figures in `REG` themselves still need checking by a lawyer, and five of its lines
  have no source yet.
- **Privacy:** photos and descriptions are sent to Meta.
  - The data sent with `citizen_update` doesn't include names.
  - `full_report` and `stage_assist` send `ticket_ctx`; check what it contains if personal data matters.
- **Quota:** the 30 calls per hour limit is kept in memory. It resets when the server restarts, and it only works with
  a single server process.
- **Cost:** every button press is one paid call (two if the JSON answer has to be retried). Triage runs once per
  citizen report, so it grows with the number of reports.
