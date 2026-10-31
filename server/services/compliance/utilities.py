"""Tier 3: Call-Before-You-Dig / DT-DICT alert."""
from sqlalchemy import select
from sqlalchemy.orm import Session

import adapters.utilities as utilities_adapter
from db.models.compliance import TicketUtilityAlert
from db.models.core import Ticket
from services.compliance.jurisdiction import jurisdiction_for


def submit_alert(db: Session, ticket: Ticket) -> dict:
    j = jurisdiction_for(db, ticket)
    cfg = (j.config or {}).get('utility_alert')
    if not cfg or ticket.category not in cfg.get('required_for_categories', []):
        return {'applicable': False}
    existing = db.scalar(select(TicketUtilityAlert).where(
        TicketUtilityAlert.ticket_id == ticket.id, TicketUtilityAlert.status.in_(['sent', 'responses_received'])))
    if existing:
        return {'applicable': True, 'alert_ref': existing.alert_ref, 'reused': True}
    res = utilities_adapter.get_provider().submit_alert(
        ticket_ref=ticket.public_ref, lat=ticket.lat, lng=ticket.lng, provider=cfg['provider'],
        response_days=cfg.get('response_days', 9), valid_months=cfg.get('receipt_valid_months', 3))
    db.add(TicketUtilityAlert(ticket_id=ticket.id, provider=res['provider'], alert_ref=res['alert_ref'],
                              operators=res.get('operators'), status='sent', valid_until=res.get('valid_until')))
    return {'applicable': True, 'alert_ref': res['alert_ref'], 'simulated': res.get('simulated', False)}


def record_failure(db: Session, ticket: Ticket, exc: Exception) -> None:
    """Called by the pipeline after the retries are exhausted: keep a 'failed' row for ops."""
    try:
        provider = ((jurisdiction_for(db, ticket).config or {}).get('utility_alert') or {}).get('provider', 'unknown')
    except Exception:  # noqa: BLE001
        provider = 'unknown'
    db.add(TicketUtilityAlert(ticket_id=ticket.id, provider=provider, status='failed'))
    db.commit()
