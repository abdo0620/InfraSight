"""Plain-language updates for the citizens who reported or follow a ticket, written by the AI in each citizen's
language. Runs after the request (FastAPI BackgroundTasks), so staff never wait for it."""
import logging
from fastapi import HTTPException
from ..db import Notification, SessionLocal, Ticket, User
from ..regulations import STAGES
from . import ai


def citizens(t: Ticket) -> set[int]:
    return ({t.reporter_id} | set((t.data or {}).get("followers") or [])) - {None}


def notify(ref: str, event: str, user_ids: set[int] | None = None) -> None:
    with SessionLocal() as s:
        t = s.get(Ticket, ref)
        if not t:
            return
        users = s.query(User).filter(User.id.in_(user_ids if user_ids is not None else citizens(t))).all()
        nxt = STAGES[t.st]["n"] if t.st < len(STAGES) else None
        info = {"ref": t.ref, "title": t.title, "address": t.addr, "description": t.desc}
        texts: dict[str, str] = {}
        for u in users:
            if u.lang not in texts:
                texts[u.lang] = f"{t.ref} · {t.title}: {event}." + (f" Next step: {nxt}." if nxt else "")
                if ai.configured():
                    try:
                        texts[u.lang] = ai.citizen_update(u.lang, info, event, nxt)
                    except HTTPException as e:    # keep the plain message
                        logging.warning("Citizen update for %s not written by AI: %s", ref, e.detail)
            s.add(Notification(user_id=u.id, ref=t.ref, text=texts[u.lang]))
        s.commit()
