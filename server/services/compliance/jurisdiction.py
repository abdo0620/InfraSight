"""Tier 3: resolve the jurisdiction for a ticket's location."""
from sqlalchemy import select
from sqlalchemy.orm import Session

import adapters.jurisdiction as jurisdiction_adapter
import adapters.zoning as zoning_adapter
from db.models.compliance import Jurisdiction, TicketCompliance
from db.models.core import Ticket
from services.core.errors import NoMatch


def get_or_create_compliance(db: Session, ticket: Ticket) -> TicketCompliance:
    row = db.get(TicketCompliance, ticket.id)
    if not row:
        row = TicketCompliance(ticket_id=ticket.id, status='pending')
        db.add(row)
    return row


def resolve(db: Session, ticket: Ticket) -> dict:
    hit = jurisdiction_adapter.get_provider().locate(ticket.lat, ticket.lng)
    if not hit:
        raise NoMatch('no jurisdiction contains this location')
    j = db.scalar(select(Jurisdiction).where(Jurisdiction.code == hit['code'], Jurisdiction.is_active.is_(True)))
    if not j:
        raise NoMatch(f"jurisdiction '{hit['code']}' is not seeded or inactive")
    try:  # zoning is a bonus: its failure never fails the jurisdiction step
        zoning = zoning_adapter.get_provider().zone_for(ticket.lat, ticket.lng)
    except Exception:  # noqa: BLE001
        zoning = None
    row = get_or_create_compliance(db, ticket)
    row.jurisdiction_id, row.jurisdiction_confidence, row.zoning_result = j.id, hit.get('confidence'), zoning
    row.status = 'in_progress'
    return {'jurisdiction': j.code, 'confidence': hit.get('confidence')}


def jurisdiction_for(db: Session, ticket: Ticket) -> Jurisdiction:
    comp = db.get(TicketCompliance, ticket.id)
    if not comp or not comp.jurisdiction_id:
        raise NoMatch('jurisdiction not resolved for this ticket')
    return db.get(Jurisdiction, comp.jurisdiction_id)
