"""Hotspots and their AI forecast, the weekly brief for elected officials, citizens' notifications."""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..auth import ai_quota, current_user, staff, user_label
from ..db import Insight, Notification, Ticket, User, get_db
from ..regulations import DECISION_STAGE
from ..services import ai

router = APIRouter(prefix="/api", tags=["insights"])


def _mid(t: Ticket) -> float:
    return (t.cost_min + t.cost_max) / 2 if t.cost_min is not None else 0


def _latest(s: Session, kind: str) -> dict | None:
    i = s.query(Insight).filter_by(kind=kind).order_by(Insight.id.desc()).first()
    return i and {**i.data, "created": i.created.isoformat(timespec="minutes"), "by": i.by}


def hotspots(s: Session) -> list[dict]:
    """Streets with 2 or more reports over the last 12 months (merged duplicates excluded), most worrying first."""
    now, groups = datetime.utcnow(), defaultdict(list)
    for t in s.query(Ticket).filter(Ticket.created >= now - timedelta(days=365)):
        d = t.data or {}
        if d.get("street_name") and not d.get("merged_into"):
            groups[d["street_name"]].append(t)
    out = []
    for street, ts in groups.items():
        if len(ts) < 2:
            continue
        pts = [(t.lat, t.lng) for t in ts if t.lat is not None]
        out.append({"street": street, "count": len(ts), "open": sum(t.st < 7 for t in ts),
                    "types": dict(Counter(t.type for t in ts)), "avg_severity": round(sum(t.sev for t in ts) / len(ts), 1),
                    "cost_eur": round(sum(_mid(t) for t in ts)), "first": min(t.created for t in ts).date().isoformat(),
                    "last": max(t.created for t in ts).date().isoformat(), "refs": [t.ref for t in ts],
                    "lat": sum(p[0] for p in pts) / len(pts) if pts else None,
                    "lng": sum(p[1] for p in pts) / len(pts) if pts else None,
                    # recent and severe reports weigh more
                    "score": round(sum(t.sev * (1 if (now - t.created).days < 90 else .5) for t in ts), 1)})
    return sorted(out, key=lambda h: -h["score"])


@router.get("/hotspots")
def get_hotspots(_u: User = Depends(staff), s: Session = Depends(get_db)):
    return {"hotspots": hotspots(s), "forecast": _latest(s, "forecast")}


@router.post("/hotspots/forecast")
def make_forecast(u: User = Depends(staff), _q: User = Depends(ai_quota), s: Session = Depends(get_db)):
    hs = [{k: v for k, v in h.items() if k not in ("lat", "lng", "refs")} for h in hotspots(s)[:10]]
    f = ai.forecast(hs, date.today().strftime("%B %Y")).model_dump()
    s.add(Insight(kind="forecast", by=user_label(u), data=f))
    s.commit()
    return {"hotspots": hotspots(s), "forecast": _latest(s, "forecast")}


def week_facts(s: Session) -> dict:
    today = date.today()
    start = today - timedelta(days=7)
    ts = s.query(Ticket).all()
    live = [t for t in ts if not (t.data or {}).get("merged_into")]
    new = [t for t in live if t.created.date() >= start]
    opened = [t for t in live if t.st < 7]
    closed = [t for t in live if any(a.e.startswith("Stage completed: Acceptance") and a.d >= start.isoformat()
                                     for a in t.audit)]
    line = lambda t: f"{t.ref} {t.title} ({t.addr}), severity {t.sev}"
    return {"period": f"{start} to {today}", "new_reports": len(new), "new_by_type": dict(Counter(t.type for t in new)),
            "closed_this_week": [line(t) for t in closed], "open_total": len(opened),
            "high_severity_open": [line(t) for t in opened if t.sev >= 4],
            "blocked_streets": [line(t) for t in opened if ((t.data or {}).get("cons") or {}).get("blocked_access")],
            "past_deadline": [line(t) for t in opened if t.due < 0],
            "awaiting_elected_signature": [line(t) for t in opened if t.st == DECISION_STAGE],
            "committed_estimate_eur": round(sum(_mid(t) for t in opened if t.st >= DECISION_STAGE)),
            "duplicates_merged": sum(1 for t in ts if (t.data or {}).get("merged_into")),
            "hotspots": [f"{h['street']}: {h['count']} reports" for h in hotspots(s)[:3]]}


@router.get("/brief")
def get_brief(_u: User = Depends(staff), s: Session = Depends(get_db)):
    return {"brief": _latest(s, "weekly"), "facts": week_facts(s)}


@router.post("/brief")
def make_brief(u: User = Depends(staff), _q: User = Depends(ai_quota), s: Session = Depends(get_db)):
    facts = week_facts(s)
    s.add(Insight(kind="weekly", by=user_label(u), data={"text": ai.weekly_brief(facts), "facts": facts}))
    s.commit()
    return {"brief": _latest(s, "weekly"), "facts": facts}


@router.get("/notifications")
def notifications(u: User = Depends(current_user), s: Session = Depends(get_db)):
    q = s.query(Notification).filter_by(user_id=u.id)
    rows = q.order_by(Notification.id.desc()).limit(50).all()
    return {"unread": q.filter_by(read=False).count(),
            "items": [{"ref": n.ref, "text": n.text, "date": n.created.date().isoformat(), "read": n.read} for n in rows]}


@router.post("/notifications/read")
def mark_read(u: User = Depends(current_user), s: Session = Depends(get_db)):
    s.query(Notification).filter_by(user_id=u.id, read=False).update({"read": True})
    s.commit()
    return {"ok": True}
