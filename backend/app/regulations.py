"""Pipeline stages, directory and regulatory notes. Single source: the frontend loads them from GET /api/meta.
TODO: have the legal department validate every figure."""

REG = (
    "Procurement: works under EUR 100,000 excl. VAT may be awarded without publicity or competition (art. R2122-8 "
    "Code de la commande publique, decree 2025-1386, in force 1 Jan 2026), but the buyer must not always pick the same "
    "firm. Supplies and services: threshold EUR 60,000 from 1 Apr 2026. Above the thresholds: adapted procedure with "
    "electronic submission; publication in BOAMP or a legal gazette from about EUR 90,000 [verify]. EU formal procedure "
    "thresholds 2026-2027: works EUR 5,404,000, local authority supplies and services EUR 216,000. Council deliberation "
    "is needed for major works and credits; the mayor may decide within council delegations (L2122-22 CGCT). Before "
    "digging: DT and DICT via the national one-stop shop. Traffic and parking order by the mayor (L2213-1 CGCT), posted "
    "on site. Acceptance report starts the 1-year completion warranty (Civil Code 1792-6). Payment within 30 days; "
    "retention up to 5%. Ownership: only communal public domain is the commune's responsibility; otherwise inform "
    "Département, State (DIR), EPCI, operator or private owner."
)

# n: name, who, legal, docs, sla, c: checklist, p: AI task for the stage (kept on the server, not sent to the browser)
STAGES = [
    {"n": "Intake and registration", "who": "Citizen, agent, CRM system",
     "legal": "Unique ticket number for traceability. GDPR notice for personal data. Pre-qualification to the competent department.",
     "docs": "Ticket, photo, geolocation", "sla": "Acknowledge within 2 working days",
     "c": ["Unique ticket number issued", "Routed to the competent department", "Duplicates checked", "Citizen acknowledged"],
     "p": "Check the intake: classify type and severity, detect missing information, check duplicates against other open tickets, and draft the acknowledgement message to the citizen."},
    {"n": "Technical and financial study", "who": "Technicians, engineers, legal department",
     "legal": "Verify the land is communal public domain, not State, Département, EPCI or private. Estimate materials and labour.",
     "docs": "Inspection report, cost estimate, cadastre extract", "sla": "Inspection within 5 working days (24 h if danger)",
     "c": ["Site inspection done", "Cost estimate recorded", "Ownership verified (cadastre)", "Safety measures taken if danger"],
     "p": "Prepare the study: inspection checklist, ownership verification steps (communal public domain or not), cost range with assumptions, and who must be informed if the land is not municipal."},
    {"n": "Arbitration and decision", "who": "Service director, delegated councillor, municipal council",
     "legal": "Budget must cover the spend. Small repairs: purchase order signed by the service head. Major works: council deliberation and vote of credits (CGCT). The mayor decides within council delegations (art. L2122-22 CGCT).",
     "docs": "Purchase order or deliberation note", "sla": "Council agenda set per meeting calendar",
     "c": ["Budget line identified", "Priority score validated", "Decision route chosen (order or council)", "Elected sign-off recorded"],
     "p": "Draft the decision memo: budget impact, priority rationale, whether a purchase order or a council deliberation is needed (give the legal basis), and a draft purchase order or deliberation summary."},
    {"n": "Public procurement", "who": "Procurement unit, award committee",
     "legal": "Code de la commande publique. Works under €100,000 HT: no publicity or competition required (art. R2122-8, decree 2025-1386, since 1 Jan 2026), but do not always pick the same firm. Above: adapted procedure, electronic submission. EU works threshold €5,404,000 HT (2026-2027).",
     "docs": "CCTP, quotes or tender file, award report, notification", "sla": "Per procedure; notification before any order",
     "c": ["CCTP written", "Mode chosen against thresholds", "Offers analysed", "Contract notified"],
     "p": "Draft the CCTP outline with applicable standards, choose the procurement mode using the thresholds for this estimated amount, and list documents to prepare and evaluation criteria."},
    {"n": "Authorizations", "who": "Mayor, network operators",
     "legal": "DT and DICT through the national one-stop shop before digging. Traffic and parking order by the mayor (CGCT art. L2213-1), posted on site in advance.",
     "docs": "DT-DICT receipts, traffic order, signage plan", "sla": "Post the order before works start",
     "c": ["DT-DICT sent to operators", "Operator replies received", "Traffic order signed", "Order posted on site"],
     "p": "Prepare authorizations: DT-DICT checklist with the network operators to query, a draft traffic and parking order with articles, and the signage and public information plan."},
    {"n": "Execution and monitoring", "who": "Contractor, site inspector",
     "legal": "Service order (OS) fixes the start date. Visits check materials and methods against the CCTP. Temporary signage must stay compliant.",
     "docs": "Service order, site reports, photos", "sla": "Regular visits until completion",
     "c": ["Service order issued", "Start date confirmed", "Site visits logged", "Signage checked"],
     "p": "Prepare site monitoring: service order content, inspection checkpoints against the CCTP, safety and signage checks, and a photo evidence list."},
    {"n": "Acceptance and closure", "who": "Mayor or delegate, contractor, accounting",
     "legal": "Pre-acceptance inspection (OPR), then acceptance report (PV) starting the 1-year completion warranty (Civil Code art. 1792-6). Final statement (DGD), payment within the 30-day public payment delay, retention up to 5%.",
     "docs": "PV, final statement, invoice", "sla": "Payment within 30 days",
     "c": ["OPR inspection done", "Acceptance report signed", "Invoice checked and sent to the Treasury", "Citizen informed, ticket closed"],
     "p": "Prepare closure: OPR checklist, draft acceptance report (PV) with warranty start, final statement and payment steps, and the message that closes the ticket and informs the citizen."},
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
