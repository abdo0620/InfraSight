"""Pipeline stages, directory and regulatory notes. Single source: the frontend loads them from GET /api/meta.
TODO: have the legal department validate every figure."""

# Regulatory notes given to the AI. One rule per line, each ending with its source in parentheses, so the AI can cite
# it (see SOURCING in services/ai.py). "source not stated [verify]" = no reference yet: the AI must flag the point.
REG = "\n".join([
    "- Works under EUR 100,000 excl. VAT may be awarded without publicity or competition, but the buyer must not "
    "always choose the same firm. (art. R2122-8 Code de la commande publique; decree 2025-1386, in force 1 Jan 2026)",
    "- Supplies and services: the same exemption applies under EUR 60,000 excl. VAT from 1 Apr 2026. "
    "(source not stated [verify])",
    "- Above these thresholds: adapted procedure with electronic submission. (Code de la commande publique)",
    "- Publication in the BOAMP or a legal gazette from about EUR 90,000. (source not stated [verify])",
    "- EU formal procedure thresholds 2026-2027: works EUR 5,404,000; local authority supplies and services "
    "EUR 216,000. (EU thresholds 2026-2027)",
    "- Major works and credits need a council deliberation; the mayor may decide within the delegations granted by "
    "the council. (art. L2122-22 CGCT)",
    "- Before digging: DT and DICT declarations through the national one-stop shop. (source not stated [verify])",
    "- Traffic and parking order by the mayor, posted on site. (art. L2213-1 CGCT)",
    "- The acceptance report starts the 1-year completion warranty. (art. 1792-6 Code civil)",
    "- Payment within 30 days; retention of up to 5%. (source not stated [verify])",
    "- Ownership: only the communal public domain is the commune's responsibility; otherwise inform the Département, "
    "the State (DIR), the EPCI, the network operator or the private owner. (source not stated [verify])",
])

# n: name, who, legal, docs, sla, c: checklist, p: AI task for the stage (kept on the server, not sent to the browser)
STAGES = [
    {"n": "Intake and registration", "who": "Citizen, agent, CRM system",
     "legal": "Unique ticket number for traceability. GDPR notice for personal data. Pre-qualification to the competent department.",
     "docs": "Ticket, photo, geolocation", "sla": "Acknowledge within 2 working days",
     "c": ["Unique ticket number issued", "Routed to the competent department", "Duplicates checked", "Citizen acknowledged"],
     "p": "Deliverables: 1. CLASSIFICATION CHECK: confirm or correct the type and severity, with a one-line reason. 2. MISSING INFORMATION: what staff still need to act (exact location, size, access, immediate danger), or \"none\". 3. DUPLICATES: any open ticket that describes the same problem at the same place, with its ref and the reason, or \"none\". 4. ACKNOWLEDGEMENT: the message to the citizen, max 50 words, plain words, with the ticket reference and no promised dates."},
    {"n": "Technical and financial study", "who": "Technicians, engineers, legal department",
     "legal": "Verify the land is communal public domain, not State, Département, EPCI or private. Estimate materials and labour.",
     "docs": "Inspection report, cost estimate, cadastre extract", "sla": "Inspection within 5 working days (24 h if danger)",
     "c": ["Site inspection done", "Cost estimate recorded", "Ownership verified (cadastre)", "Safety measures taken if danger"],
     "p": "Deliverables: 1. INSPECTION CHECKLIST: 4 to 6 points to check on site. 2. OWNERSHIP CHECK: how to confirm the land is communal public domain (cadastre, road classification) and who to inform if it is not. 3. COST RANGE: minimum and maximum in EUR excl. VAT, with the quantities and unit rates assumed, marked [verify]. 4. SAFETY: interim measures if severity is 4 or 5, otherwise \"none needed\"."},
    {"n": "Arbitration and decision", "who": "Service director, delegated councillor, municipal council",
     "legal": "Budget must cover the spend. Small repairs: purchase order signed by the service head. Major works: council deliberation and vote of credits (CGCT). The mayor decides within council delegations (art. L2122-22 CGCT).",
     "docs": "Purchase order or deliberation note", "sla": "Council agenda set per meeting calendar",
     "c": ["Budget line identified", "Priority score validated", "Decision route chosen (order or council)", "Elected sign-off recorded"],
     "p": "Deliverables: 1. BUDGET IMPACT: amount and budget line [to fill]. 2. PRIORITY RATIONALE: from severity, urgency and who is exposed. 3. DECISION ROUTE: purchase order within the mayor's delegations, or council deliberation, with the legal basis. 4. DRAFT: the purchase order, or a summary of the deliberation."},
    {"n": "Public procurement", "who": "Procurement unit, award committee",
     "legal": "Code de la commande publique. Works under €100,000 HT: no publicity or competition required (art. R2122-8, decree 2025-1386, since 1 Jan 2026), but do not always pick the same firm. Above: adapted procedure, electronic submission. EU works threshold €5,404,000 HT (2026-2027).",
     "docs": "CCTP, quotes or tender file, award report, notification", "sla": "Per procedure; notification before any order",
     "c": ["CCTP written", "Mode chosen against thresholds", "Offers analysed", "Contract notified"],
     "p": "Deliverables: 1. CCTP OUTLINE: the sections of the technical specification and the technical standards to apply, marked [verify]. 2. PROCUREMENT MODE: the route for the estimated amount, from the thresholds, with sources. 3. DOCUMENTS: the documents to prepare. 4. AWARD CRITERIA: 2 to 4 criteria with weights."},
    {"n": "Authorizations", "who": "Mayor, network operators",
     "legal": "DT and DICT through the national one-stop shop before digging. Traffic and parking order by the mayor (CGCT art. L2213-1), posted on site in advance.",
     "docs": "DT-DICT receipts, traffic order, signage plan", "sla": "Post the order before works start",
     "c": ["DT-DICT sent to operators", "Operator replies received", "Traffic order signed", "Order posted on site"],
     "p": "Deliverables: 1. DT-DICT CHECKLIST: the networks likely present at this address and the operators to query. 2. TRAFFIC ORDER: the key articles of the temporary traffic and parking order. 3. SIGNAGE AND INFORMATION PLAN: signs and their positions, and how residents are informed."},
    {"n": "Execution and monitoring", "who": "Contractor, site inspector",
     "legal": "Service order (OS) fixes the start date. Visits check materials and methods against the CCTP. Temporary signage must stay compliant.",
     "docs": "Service order, site reports, photos", "sla": "Regular visits until completion",
     "c": ["Service order issued", "Start date confirmed", "Site visits logged", "Signage checked"],
     "p": "Deliverables: 1. SERVICE ORDER: what it must contain. 2. INSPECTION CHECKPOINTS: what to check against the CCTP at each phase of the works. 3. SAFETY AND SIGNAGE CHECKS. 4. PHOTO EVIDENCE: the photos to take and when."},
    {"n": "Acceptance and closure", "who": "Mayor or delegate, contractor, accounting",
     "legal": "Pre-acceptance inspection (OPR), then acceptance report (PV) starting the 1-year completion warranty (Civil Code art. 1792-6). Final statement (DGD), payment within the 30-day public payment delay, retention up to 5%.",
     "docs": "PV, final statement, invoice", "sla": "Payment within 30 days",
     "c": ["OPR inspection done", "Acceptance report signed", "Invoice checked and sent to the Treasury", "Citizen informed, ticket closed"],
     "p": "Deliverables: 1. OPR CHECKLIST: points to inspect before acceptance. 2. ACCEPTANCE REPORT DRAFT: with reservations [to fill] and the start of the completion warranty, with source. 3. FINAL STATEMENT AND PAYMENT: the steps and deadlines, with sources. 4. CLOSING MESSAGE: to the citizen, max 50 words, plain words."},
]
DECISION_STAGE = 2                     # only an elected official may sign it

DIRECTORY = [
    {"n": "Commune – Roads department", "f": "Municipal roads, pavements, signage", "h": "Ticket, then technician on site", "s": "Inspection within 5 working days"},
    {"n": "Commune – Green spaces department", "f": "Trees, parks, verges, cycle path edges", "h": "Ticket, then field team", "s": "Inspection within 5 working days"},
    {"n": "Commune – Public lighting", "f": "Streetlights and signals", "h": "Ticket, then electrician", "s": "Repair within 10 working days"},
    {"n": "Département – Road service", "f": "Departmental roads (RD)", "h": "Written notice from the mayor; shared safety measures", "s": "Per departmental agreement"},
    {"n": "State – DIR", "f": "National roads", "h": "Notice from the mayor to the DIR", "s": "Per regional protocol"},
    {"n": "Intercommunality – Waste and water", "f": "Collection, sewers, drinking water (if transferred)", "h": "Transfer the ticket to the EPCI service", "s": "Per EPCI charter"},
    {"n": "Network operators", "f": "Gas, electricity, water, telecom networks", "h": "DT-DICT through the national one-stop shop", "s": "Statutory reply times"},
    {"n": "Private owner or building manager", "f": "Private land and frontage", "h": "Formal notice; mayor police powers if danger", "s": "Set in the notice"},
    {"n": "Municipal police and emergency services (112)", "f": "Immediate danger, enforcement", "h": "Phone first, then ticket", "s": "Immediate"},
]

OWNERS = {"commune": "Commune (municipal domain)", "department": "Département (departmental road)",
          "state": "State (national road, DIR)", "epci": "Intercommunality (EPCI)", "private": "Private owner",
          "network": "Network operator"}


def public_meta() -> dict:
    """What the browser needs to render stages and the directory (no AI prompts)."""
    return {"stages": [{k: v for k, v in s.items() if k != "p"} for s in STAGES], "directory": DIRECTORY,
            "owners": OWNERS, "decision_stage": DECISION_STAGE}
