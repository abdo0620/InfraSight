import re, secrets, threading
from datetime import date, datetime
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..auth import STAFF, ai_quota, check_image, current_user, staff, user_label
from ..config import settings
from ..db import Audit, Ticket, User, Zone, get_db
from ..regulations import DECISION_STAGE, OWNERS, STAGES
from ..schemas import Triage
from ..serializers import is_own, stage_name, ticket_ctx, to_front
from ..services import ai, export, geo, images, routing, vision, visuals
from ..services.notify import citizens, notify

router = APIRouter(prefix="/api", tags=["tickets"])
_new_id = threading.Lock()             # one ticket number at a time (single process)
AI_TAG = " [AI-generated, human review required]"


def _get(s: Session, ref: str) -> Ticket:
    t = s.get(Ticket, ref)
    if not t:
        raise HTTPException(404, "Ticket not found")
    return t


def _visible(t: Ticket, u: User) -> Ticket:
    if u.role not in STAFF and not is_own(t, u):
        raise HTTPException(404, "Ticket not found")
    return t


def _log(t: Ticket, u: User | None, event: str, by_ai=False, with_img=False, image_path: str | None = None) -> None:
    t.audit.append(Audit(d=date.today().isoformat(), user_id=u.id if u else None, has_img=with_img, image_path=image_path,
                         w="AI assistant" if by_ai else user_label(u), e=event + (AI_TAG if by_ai else "")))


def _photo(t: Ticket) -> bytes | None:
    return Path(t.image_path).read_bytes() if t.image_path and Path(t.image_path).exists() else None


def _save_photo(ref: str, img: bytes, suffix: str = "") -> str:
    path = Path(settings.upload_dir) / f"{ref}{suffix}.jpg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(img)
    return str(path)


def _open(s: Session) -> list[Ticket]:
    return s.query(Ticket).filter(Ticket.st < 7).all()


def _set_data(t: Ticket, **kw) -> None:
    t.data = {**(t.data or {}), **kw}  # reassign so SQLAlchemy sees the JSON change


def _zone(t: Ticket) -> dict | None:
    d = t.data or {}
    return ((d.get("rep") or {}).get("danger_zone")) or d.get("zone")


def _brief(t: Ticket) -> dict:
    return {"ref": t.ref, "title": t.title, "type": t.type, "address": t.addr, "description": t.desc}


@router.get("/state")
def state(u: User = Depends(current_user), s: Session = Depends(get_db)):
    """Everything the console needs at startup, filtered for this user."""
    zones = [{"id": z.id, "name": z.name, "level": z.level, "points": z.points, "source": z.source} for z in s.query(Zone)]
    return {"tickets": [to_front(t, u) for t in s.query(Ticket).order_by(Ticket.created.desc())], "zones": zones}


@router.get("/tickets/{ref}")
def one(ref: str, u: User = Depends(current_user), s: Session = Depends(get_db)):
    return to_front(_visible(_get(s, ref), u), u)


@router.post("/tickets")
async def create(bg: BackgroundTasks, addr: str = Form(..., min_length=1, max_length=200),
                 desc: str = Form(..., min_length=1, max_length=4000), lat: float | None = Form(None),
                 lng: float | None = Form(None), image: UploadFile | None = File(None),
                 u: User = Depends(ai_quota), s: Session = Depends(get_db)):
    """A citizen report. The server assigns the number, stores the photo and runs the AI triage. If the AI finds the
    same problem in an open ticket close by, the report is added to that ticket instead (duplicate merging)."""
    img = images.normalize(await image.read()) if image and image.filename else None
    road = None
    if lat is not None and lng is not None:
        found, road = await run_in_threadpool(geo.place, lat, lng)
        if addr.startswith("Map pin"):  # default text of the map form
            addr = found or addr
    near = sorted(((geo.distance((lat, lng), (o.lat, o.lng)) if lat is not None and o.lat is not None else None, o)
                   for o in _open(s)), key=lambda x: (x[0] is None, x[0] or 0))
    others = [f"{o.ref} {o.title}, {o.addr}" + (f" ({round(d)} m away)" if d is not None else "") for d, o in near[:20]]
    x, ai_error, zone = None, None, None
    try:                               # slow network calls run in a thread, so other users are not blocked
        x = await run_in_threadpool(ai.triage, addr, desc, others, img)
        zone = await run_in_threadpool(geo.shape_zone, x.danger_zone.model_dump(), lat, lng)
    except HTTPException as e:
        ai_error = e.detail + " Your report is saved for manual triage."
    dup = re.search(r"[A-Z]{2}-\d{4}", x.duplicate_of or "") if x else None
    target = next((o for d, o in near if dup and o.ref == dup.group(0) and d is not None
                   and d <= settings.duplicate_radius_m), None)
    if target:
        _merge_report(target, u, desc, img, x)
        s.commit()
        bg.add_task(notify, target.ref, "Your report was added to an existing case about the same problem, already "
                                        "being handled", {u.id})
        return {"ticket": to_front(target, u), "merged_into": target.ref, "ai_error": None}
    with _new_id:
        nid = max(50, (s.query(func.max(Ticket.id)).scalar() or 0) + 1)
        ref = f"IS-{nid:04d}"
        t = Ticket(ref=ref, id=nid, title=x.title if x else desc[:48], type=x.type if x else "Unclassified",
                   addr=addr, owner=x.owner if x else "commune", reporter_id=u.id, desc=desc, lat=lat, lng=lng, st=0,
                   sev=x.severity if x else 3, urg=x.urgency if x else 3, due=2, cost_min=None, cost_max=None,
                   created=datetime.utcnow(), image_path=_save_photo(ref, img) if img else None,
                   data={"cons": x.consequences.model_dump() if x else None, "street_name": road,
                         "zone": zone, "rep": None, "ai": {}, "ch": {}})
        _log(t, u, "Report received via the citizen portal")
        if img:
            _log(t, u, "Photo attached by the citizen", with_img=True)
        if x:
            _log(t, u, f"AI triage: {x.summary} Owner: {OWNERS[t.owner]}"
                       + (f". Possible duplicate of {x.duplicate_of} (not merged: too far or not open)" if dup else "")
                       + f". Danger: {x.consequences.danger_type}", by_ai=True)
        if img and x and x.damage_box:
            _log(t, u, "Damage zone marked on the photo", by_ai=True, image_path=visuals.set_zone(t, img, box=x.damage_box))
        want_preview = bool(img and ai.configured())
        if want_preview:
            _set_data(t, visual={**(t.data or {}).get("visual", {}), "pending": True})
        s.add(t)
        s.commit()
    bg.add_task(notify, t.ref, "Your report was received and registered")
    if want_preview:
        bg.add_task(visuals.preview_later, t.ref)
    return {"ticket": to_front(t, u), "merged_into": None, "ai_error": ai_error}


def _merge_report(t: Ticket, u: User, desc: str, img: bytes | None, x: Triage) -> None:
    """A second citizen report of the same problem: the citizen follows the ticket, the report goes in its history."""
    _set_data(t, followers=sorted(set((t.data or {}).get("followers") or []) | ({u.id} - {t.reporter_id})))
    path = _save_photo(t.ref, img, "-" + secrets.token_hex(3)) if img else None
    _log(t, u, f"Same problem reported again by a citizen: {desc}", image_path=path)
    _log(t, u, f"AI merged this report into {t.ref} (same problem, {x.summary})", by_ai=True)
    if x.severity > t.sev:
        t.sev = x.severity
        _log(t, u, f"Severity raised to {t.sev} after the new report", by_ai=True)


class Merge(BaseModel):
    into: str


@router.post("/tickets/{ref}/merge")
def merge(ref: str, m: Merge, bg: BackgroundTasks, u: User = Depends(staff), s: Session = Depends(get_db)):
    """Staff merge a duplicate ticket into another: its citizens follow the target, the duplicate is closed."""
    src, dst = _get(s, ref), _get(s, m.into)
    if src.ref == dst.ref or src.st >= 7 or dst.st >= 7:
        raise HTTPException(409, "Both tickets must be open and different")
    moved = citizens(src)
    _set_data(dst, followers=sorted((set((dst.data or {}).get("followers") or []) | moved) - {dst.reporter_id}))
    _log(dst, u, f"Merged {src.ref} into this ticket (same problem): {src.title}. {src.desc}", image_path=src.image_path)
    if src.sev > dst.sev:
        dst.sev = src.sev
    _set_data(src, merged_into=dst.ref)
    _log(src, u, f"Merged into {dst.ref} (same problem)")
    src.st = 7
    s.commit()
    bg.add_task(notify, dst.ref, f"Your report {src.ref} was combined with {dst.ref}, which handles the same problem",
                moved)
    return to_front(dst, u)


@router.get("/files/{name}")
def file(name: str, exp: int, sig: str):
    """Photo links signed by the server (see auth.sign_image): <img> tags cannot send the login token."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+\.jpg", name) or not check_image(name, exp, sig):
        raise HTTPException(403, "Link expired, reload the page")
    path = Path(settings.upload_dir) / name
    if not path.exists():
        raise HTTPException(404, "No photo")
    return FileResponse(path, media_type="image/jpeg")


@router.post("/tickets/{ref}/report")
def report(ref: str, u: User = Depends(staff), _q: User = Depends(ai_quota), s: Session = Depends(get_db)):
    """Full AI report (photo included)."""
    t = _get(s, ref)
    zone = visuals.read(((t.data or {}).get("visual") or {}).get("zone"))
    r = ai.full_report(ticket_ctx(t, _open(s)), _photo(t), zone).model_dump()
    r["danger_zone"] = geo.shape_zone(r["danger_zone"], t.lat, t.lng)
    _set_data(t, rep=r)
    _log(t, u, f"Full report generated: severity {r['severity']}, contact {r['authority']['primary'] or 'n/a'}", by_ai=True)
    s.commit()
    return to_front(t, u)


@router.post("/tickets/{ref}/damage")
def damage(ref: str, u: User = Depends(staff), _q: User = Depends(ai_quota), s: Session = Depends(get_db)):
    """SAM 3.1 outlines the damage on the photo (Meta Model API, or your own server with SAM_URL), then the AI
    estimates its real size."""
    t = _get(s, ref)
    img = _photo(t)
    if not img:
        raise HTTPException(409, "This ticket has no photo")
    size, err = None, None
    try:
        objects = vision.outline(img, t.type)
    except HTTPException as e:            # no outline: the AI still locates and measures the damage
        objects, err = None, e.detail
    try:
        size = ai.estimate_size(img, t.type, objects).model_dump()
    except HTTPException as e:
        err = " ".join(x for x in (err, e.detail) if x)
    if objects is None and size is None:
        raise HTTPException(503, f"Set SAM_URL or the AI key in backend/.env. {err}")
    _set_data(t, damage={"objects": objects or [], "size": size, "sam": objects is not None})
    zone = visuals.set_zone(t, img, objects, (size or {}).get("box"))
    _log(t, u, "Damage analysed: " + (f"{len(objects)} area(s) outlined by SAM 3.1. " if objects is not None else "")
         + (f"About {size['width_m']} × {size['length_m']} m ({size['confidence']} confidence)" if size else ""),
         by_ai=True, image_path=zone)
    try:
        _log(t, u, "Repair preview drawn (illustration)", by_ai=True, image_path=visuals.make_preview(t))
    except HTTPException as e:
        err = " ".join(x for x in (err, f"Repair preview: {e.detail}") if x)
    s.commit()
    return to_front(t, u) | {"ai_error": err}


@router.post("/tickets/{ref}/preview")
def preview(ref: str, u: User = Depends(staff), _q: User = Depends(ai_quota), s: Session = Depends(get_db)):
    """New repair preview (Muse Image) from the photo and the current damage zone."""
    t = _get(s, ref)
    _log(t, u, "Repair preview drawn again (illustration)", by_ai=True, image_path=visuals.make_preview(t))
    s.commit()
    return to_front(t, u)


@router.post("/tickets/{ref}/after-photo")
async def after_photo(ref: str, image: UploadFile = File(...), u: User = Depends(staff),
                      _q: User = Depends(ai_quota), s: Session = Depends(get_db)):
    """After-repair photo at closing time; the AI compares it with the citizen's photo."""
    t = _get(s, ref)
    img = images.normalize(await image.read())
    path = _save_photo(t.ref, img, "-after-" + secrets.token_hex(3))
    _log(t, u, "After-repair photo added", image_path=path)
    check, err = None, None
    try:
        zone = visuals.read(((t.data or {}).get("visual") or {}).get("zone"))
        check = (await run_in_threadpool(ai.check_repair, zone or _photo(t), img, _brief(t), bool(zone))).model_dump()
        _log(t, u, f"Repair check: {check['verdict'].replace('_', ' ')}. {check['explanation']}", by_ai=True)
    except HTTPException as e:
        err = e.detail
    _set_data(t, after={"path": path, "check": check})
    s.commit()
    return to_front(t, u) | {"ai_error": err}


@router.post("/tickets/{ref}/detour")
def detour(ref: str, u: User = Depends(staff), _q: User = Depends(ai_quota), s: Session = Depends(get_db)):
    """Detour around a blocked street (OpenStreetMap road network), then the AI drafts the mayor's traffic order."""
    t = _get(s, ref)
    z = _zone(t) or {}
    street = z.get("street")
    if z.get("shape") != "street" or not street:
        raise HTTPException(409, "A detour needs a street danger zone with its street shape")
    try:
        d = routing.detour(street["lines"])
    except RuntimeError as e:
        raise HTTPException(502, str(e))
    order, err = None, None
    try:
        order = ai.traffic_order(_brief(t), street.get("name") or t.addr, z.get("radius_m") or 0, d["streets"])
    except HTTPException as e:
        err = e.detail
    _set_data(t, detour={**d, "order": order})
    _log(t, u, f"Detour computed: {d['length_m']} m via {', '.join(d['streets']) or 'local roads'}"
               + (". Traffic order drafted" if order else ""), by_ai=bool(order))
    s.commit()
    return to_front(t, u) | {"ai_error": err}


@router.post("/tickets/{ref}/stages/{stage}/assist")
def assist(ref: str, stage: int, u: User = Depends(staff), _q: User = Depends(ai_quota), s: Session = Depends(get_db)):
    t = _get(s, ref)
    if stage != t.st:
        raise HTTPException(409, "AI assist is only available for the current stage")
    text = ai.stage_assist(stage, ticket_ctx(t, _open(s)), _photo(t))
    _set_data(t, ai={**(t.data or {}).get("ai", {}), str(stage): text})
    _log(t, u, f"AI draft for stage: {stage_name(stage)}", by_ai=True)
    s.commit()
    return to_front(t, u)


class Check(BaseModel):
    stage: int
    item: int
    done: bool


@router.put("/tickets/{ref}/checklist")
def checklist(ref: str, c: Check, u: User = Depends(staff), s: Session = Depends(get_db)):
    t = _get(s, ref)
    if c.stage != t.st or not 0 <= c.item < len(STAGES[t.st]["c"]):
        raise HTTPException(409, "Only the current stage's checklist can be changed")
    _set_data(t, ch={**(t.data or {}).get("ch", {}), f"{c.stage}:{c.item}": int(c.done)})
    if c.done:
        _log(t, u, f"Checked: {STAGES[c.stage]['c'][c.item]}")
    s.commit()
    return to_front(t, u)


@router.post("/tickets/{ref}/advance")
def advance(ref: str, bg: BackgroundTasks, u: User = Depends(staff), s: Session = Depends(get_db)):
    t = _get(s, ref)
    if t.st >= len(STAGES):
        raise HTTPException(409, "Ticket already closed")
    ch = (t.data or {}).get("ch", {})
    if not all(ch.get(f"{t.st}:{k}") for k in range(len(STAGES[t.st]["c"]))):
        raise HTTPException(409, "Complete the checklist first")
    if t.st == DECISION_STAGE and u.role != "elected":
        raise HTTPException(403, "Only an elected official can sign the decision")
    done = stage_name(t.st)
    _log(t, u, f"Stage completed: {done}" + (" (decision signed)" if t.st == DECISION_STAGE else ""))
    t.st += 1
    t.due = 5
    s.commit()
    bg.add_task(notify, t.ref, "The repair is finished and the case is closed" if t.st >= len(STAGES)
                else f"Step completed: {done}")
    return to_front(t, u)


@router.post("/tickets/{ref}/apply-severity")
def apply_severity(ref: str, u: User = Depends(staff), s: Session = Depends(get_db)):
    t = _get(s, ref)
    rep = (t.data or {}).get("rep")
    if not rep:
        raise HTTPException(409, "Generate the AI report first")
    t.sev = min(5, max(1, int(rep["severity"])))
    _log(t, u, f"Severity set to {t.sev} from the AI report")
    s.commit()
    return to_front(t, u)


@router.get("/tickets/{ref}/report.html", response_class=HTMLResponse)
def report_html(ref: str, u: User = Depends(staff), s: Session = Depends(get_db)):
    t = _get(s, ref)
    v, after = (t.data or {}).get("visual") or {}, (t.data or {}).get("after") or {}
    return export.report_html(to_front(t, u), {"photo": t.image_path, "zone": v.get("zone"),
                                               "preview": v.get("preview"), "after": after.get("path")})   # TODO: PDF (WeasyPrint)


@router.put("/zones")
def put_zones(zones: list[dict], u: User = Depends(staff), s: Session = Depends(get_db)):
    """Replace the manually drawn zones (AI zones come from tickets, they are not stored here)."""
    s.query(Zone).delete()
    for z in zones:
        s.add(Zone(id=str(z["id"]), name=z.get("name", "Manual zone"), level=int(z["level"]), points=z["points"],
                   source=z.get("source", "manual")))
    s.commit()
    return {"count": len(zones)}
