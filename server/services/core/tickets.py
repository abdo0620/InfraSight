"""Tier 1 ticket creation and state machine."""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.models.core import Ticket, TicketEvent

TRANSITIONS = {
    'submitted': {'triaged', 'in_progress', 'rejected'},
    'triaged': {'scheduled', 'in_progress', 'rejected'},
    'scheduled': {'in_progress', 'rejected'},
    'in_progress': {'resolved'},
    'resolved': {'in_progress'},  # reopen
    'rejected': set(),
}


class InvalidTransition(ValueError):
    pass


def add_event(db: Session, ticket_id: str, event_type: str, payload: dict | None = None, actor: str = 'system') -> TicketEvent:
    ev = TicketEvent(ticket_id=ticket_id, event_type=event_type, payload=payload or {}, actor=actor)
    db.add(ev)
    return ev


def _next_ref(db: Session) -> str:
    prefix = f'INF-{datetime.now(timezone.utc).year}-'
    n = db.scalar(select(func.count()).select_from(Ticket).where(Ticket.public_ref.like(prefix + '%'))) or 0
    return f'{prefix}{n + 1:04d}'


def create_ticket(db: Session, *, lat: float, lng: float, description: str, category: str, severity: str,
                  photo_asset_id: str | None, needs_human_review: bool, actor: str = 'system:intake') -> Ticket:
    for _ in range(5):
        ticket = Ticket(public_ref=_next_ref(db), lat=lat, lng=lng, description=description, category=category,
                        severity=severity, photo_asset_id=photo_asset_id, needs_human_review=needs_human_review)
        db.add(ticket)
        try:
            db.flush()
        except IntegrityError:  # two requests picked the same ref: retry
            db.rollback()
            continue
        add_event(db, ticket.id, 'created', {'public_ref': ticket.public_ref}, actor)
        db.commit()
        return ticket
    raise RuntimeError('Could not allocate a ticket reference')


def transition(db: Session, ticket: Ticket, new_status: str, actor: str) -> Ticket:
    if new_status not in TRANSITIONS.get(ticket.status, set()):
        raise InvalidTransition(f'{ticket.status} -> {new_status} is not allowed')
    old, ticket.status = ticket.status, new_status
    add_event(db, ticket.id, 'status_change', {'from': old, 'to': new_status}, actor)
    db.commit()
    return ticket
