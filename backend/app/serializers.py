"""Database rows -> the JSON shape the frontend uses (frontend/js/app.js), filtered by who is asking."""
from datetime import date, datetime
from pathlib import Path
from .auth import STAFF, sign_image
from .db import Ticket, User
from .regulations import OWNERS, STAGES

# What a citizen sees of other people's reports (map and city-wide insights): no photo, history or AI output
PUBLIC = ("id", "ref", "title", "type", "addr", "lat", "lng", "owner", "st", "sev", "urg", "age", "desc", "cons", "zone")


def file_url(path: str | None) -> str | None:
    """Signed link to a photo in uploads/ (see auth.sign_image)."""
    if not path:
        return None
    name = Path(path).name
    return f"/api/files/{name}?{sign_image(name)}"


def is_own(t: Ticket, viewer: User) -> bool:
    """Reported it, or reported the same problem and was merged into it (follower)."""
    return t.reporter_id == viewer.id or viewer.id in ((t.data or {}).get("followers") or [])


def to_front(t: Ticket, viewer: User) -> dict:
    d = t.data or {}
    img = file_url(t.image_path)
    after = d.get("after")
    f = {"id": t.id, "ref": t.ref, "title": t.title, "type": t.type, "addr": t.addr, "lat": t.lat, "lng": t.lng,
         "owner": t.owner, "st": t.st, "sev": t.sev, "urg": t.urg, "due": t.due, "desc": t.desc,
         "cost": [t.cost_min, t.cost_max] if t.cost_min is not None else None,
         "age": (datetime.utcnow() - t.created).days, "img": img, "own": int(is_own(t, viewer)),
         "cons": d.get("cons"), "zone": d.get("zone"), "rep": d.get("rep"), "ai": d.get("ai") or {},
         "ch": d.get("ch") or {}, "damage": d.get("damage"), "detour": d.get("detour"),
         "zone_img": file_url((d.get("visual") or {}).get("zone")),
         "preview_img": file_url((d.get("visual") or {}).get("preview")),
         "preview_state": "pending" if (d.get("visual") or {}).get("pending") else (d.get("visual") or {}).get("preview_error"),
         "after": after and {**after, "img": file_url(after.get("path")), "path": None},
         "followers": len(d.get("followers") or []), "merged_into": d.get("merged_into"),
         "log": [{"d": a.d, "w": a.w, "e": a.e, "img": file_url(a.image_path) or (img if a.has_img else None)}
                 for a in t.audit]}
    if viewer.role in STAFF or f["own"]:
        return f
    return {k: f[k] for k in PUBLIC} | {"own": 0, "ai": {}, "ch": {}, "log": [], "rep": None, "img": None,
                                        "damage": None, "detour": None, "after": None, "followers": 0, "merged_into": None,
                                        "zone_img": None, "preview_img": None, "preview_state": None}


def stage_name(st: int) -> str:
    return STAGES[st]["n"] if st < len(STAGES) else "Closed"


def ticket_ctx(t: Ticket, others: list[Ticket]) -> dict:
    """Context given to the AI for the full report and the stage assistant."""
    d = t.data or {}
    rep = d.get("rep")
    return {"today": date.today().isoformat(),
            "ticket": {"ref": t.ref, "title": t.title, "type": t.type, "address": t.addr, "ownership": OWNERS.get(t.owner),
                       "description": t.desc, "severity": t.sev, "urgency": t.urg,
                       "estimated_cost_eur": [t.cost_min, t.cost_max] if t.cost_min is not None else None,
                       "stage": stage_name(t.st), "days_to_deadline": t.due,
                       "checklist_items_done": sum(1 for v in (d.get("ch") or {}).values() if v)},
            "audit": [{"d": a.d, "w": a.w, "e": a.e} for a in t.audit[-6:]],
            "report": {k: rep.get(k) for k in ("type", "severity", "authority")} if rep else None,
            "consequences": (rep or {}).get("consequences") or d.get("cons"),
            "has_photo": bool(t.image_path),
            "earlier_ai_outputs": [f"{stage_name(int(k))}: {v[:300]}" for k, v in (d.get("ai") or {}).items()],
            "other_open_tickets": [f"{o.ref} {o.title} {o.addr}" for o in others if o.ref != t.ref and o.st < 7]}
