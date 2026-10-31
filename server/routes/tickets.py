"""TIER 1 citizen view of a ticket: ID, status, SLA if known."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.admin import TicketAdmin
from db.models.core import Ticket, TicketEvent
from routes.deps import get_db
from schemas import iso

router = APIRouter(prefix='/api/tickets', tags=['tier1-tickets'])
PUBLIC_EVENTS = ('created', 'status_change')


def _by_ref(db: Session, ref: str) -> Ticket:
    t = db.scalar(select(Ticket).where(Ticket.public_ref == ref))
    if not t:
        raise HTTPException(404, 'Ticket not found')
    return t


@router.get('/{ref}')
def get_ticket(ref: str, db: Session = Depends(get_db)):
    t = _by_ref(db, ref)
    admin = db.get(TicketAdmin, t.id)  # optional enrichment: may not exist
    return {'public_ref': t.public_ref, 'status': t.status, 'category': t.category, 'severity': t.severity,
            'created_at': iso(t.created_at), 'sla_due_at': iso(admin.sla_due_at) if admin else None}


@router.get('/{ref}/events')
def get_events(ref: str, db: Session = Depends(get_db)):
    t = _by_ref(db, ref)
    evs = db.scalars(select(TicketEvent).where(TicketEvent.ticket_id == t.id, TicketEvent.event_type.in_(PUBLIC_EVENTS))
                     .order_by(TicketEvent.created_at)).all()
    return [{'type': e.event_type, 'at': iso(e.created_at), 'detail': e.payload} for e in evs]
