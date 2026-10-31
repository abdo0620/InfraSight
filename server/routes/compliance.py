"""TIER 3 endpoints. Return 501 when the tier is switched off (explicit, testable)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import feature_flags as flags
from db.models.compliance import (Jurisdiction, TicketCompliance, TicketPermitCheck, TicketSopDocument,
                                  TicketUtilityAlert)
from db.models.core import Ticket, TicketFallback
from routes.deps import get_db
from schemas import iso
from services.compliance import permits, sop, utilities
from services.core.errors import NoMatch
from services.security import require_role


def tier3_enabled():
    if not flags.is_enabled('tier3_compliance_enabled'):
        raise HTTPException(501, 'Tier 3 compliance layer is disabled')


router = APIRouter(prefix='/api/compliance', tags=['tier3-compliance'],
                   dependencies=[Depends(tier3_enabled), Depends(require_role('staff'))])


def _ticket(db: Session, ticket_id: str) -> Ticket:
    t = db.get(Ticket, ticket_id)
    if not t:
        raise HTTPException(404, 'Ticket not found')
    return t


def _guard(fn):
    try:
        return fn()
    except NoMatch as e:
        raise HTTPException(409, str(e))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f'{type(e).__name__}: {e}')


@router.get('/tickets/{ticket_id}')
def compliance_status(ticket_id: str, db: Session = Depends(get_db)):
    t = _ticket(db, ticket_id)
    comp = db.get(TicketCompliance, t.id)
    j = db.get(Jurisdiction, comp.jurisdiction_id) if comp and comp.jurisdiction_id else None
    q = lambda m: db.scalars(select(m).where(m.ticket_id == t.id)).all()  # noqa: E731
    return {
        'status': comp.status if comp else 'pending', 'jurisdiction': j.code if j else None,
        'zoning': comp.zoning_result if comp else None,
        'permits': [{'type': p.permit_type, 'status': p.status, 'requirement': p.requirement, 'source_rule': p.source_rule}
                    for p in q(TicketPermitCheck)],
        'utility_alerts': [{'provider': a.provider, 'status': a.status, 'alert_ref': a.alert_ref, 'valid_until': iso(a.valid_until)}
                           for a in q(TicketUtilityAlert)],
        'sop_documents': [{'id': d.id, 'kind': d.kind, 'version': d.version, 'human_approved': d.human_approved} for d in q(TicketSopDocument)],
        'fallbacks': [{'tier': f.tier, 'step': f.step, 'reason': f.reason, 'fallback': f.fallback} for f in q(TicketFallback)],
    }


@router.post('/tickets/{ticket_id}/permits')
def refresh_permits(ticket_id: str, db: Session = Depends(get_db)):
    t = _ticket(db, ticket_id)
    out = _guard(lambda: permits.build_checklist(db, t))
    db.commit()
    return out


@router.post('/tickets/{ticket_id}/utility-alert')
def send_utility_alert(ticket_id: str, db: Session = Depends(get_db)):
    t = _ticket(db, ticket_id)
    try:
        out = _guard(lambda: utilities.submit_alert(db, t))
    except HTTPException:
        db.rollback()
        utilities.record_failure(db, t, RuntimeError('manual submission failed'))
        raise
    db.commit()
    return out


@router.post('/tickets/{ticket_id}/sop')
def generate_sop(ticket_id: str, db: Session = Depends(get_db)):
    t = _ticket(db, ticket_id)
    out = _guard(lambda: sop.generate(db, t))
    db.commit()
    return out


@router.post('/sop/{doc_id}/approve')
def approve_sop(doc_id: str, user=Depends(require_role('staff')), db: Session = Depends(get_db)):
    try:
        doc = sop.approve(db, doc_id, f"user:{user['sub']}")
    except KeyError:
        raise HTTPException(404, 'Document not found')
    return {'id': doc.id, 'human_approved': doc.human_approved, 'approved_by': doc.approved_by}
