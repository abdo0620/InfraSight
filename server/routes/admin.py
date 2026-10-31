"""TIER 2 admin endpoints (staff only)."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import feature_flags as flags
from db.models.admin import Department, TicketAdmin, UnclassifiedQueue
from db.models.compliance import TicketCompliance
from db.models.core import Ticket
from routes.deps import get_db
from schemas import TicketPatch, iso
from services.admin import queue
from services.core import tickets
from services.security import require_role
from services.workflow import pipeline

router = APIRouter(prefix='/api/admin', tags=['tier2-admin'])
staff = Depends(require_role('staff'))
SEV_RANK = {'high': 3, 'medium': 2, 'low': 1}


def _summary(db: Session, t: Ticket) -> dict:
    admin, comp = db.get(TicketAdmin, t.id), db.get(TicketCompliance, t.id)
    dept = db.get(Department, admin.department_id) if admin and admin.department_id else None
    label = str(t.compliance_level)
    if t.compliance_level == 3 and comp and comp.status == 'degraded':
        label = '3-DEGRADED'
    return {'id': t.id, 'public_ref': t.public_ref, 'status': t.status, 'category': t.category, 'severity': t.severity,
            'needs_human_review': t.needs_human_review, 'compliance_level': t.compliance_level, 'compliance_label': label,
            'department': dept.name if dept else None, 'sla_due_at': iso(admin.sla_due_at) if admin else None,
            'in_unclassified_queue': db.scalar(select(UnclassifiedQueue.id).where(UnclassifiedQueue.ticket_id == t.id)) is not None,
            'lat': t.lat, 'lng': t.lng, 'created_at': iso(t.created_at)}


def _get(db: Session, ticket_id: str) -> Ticket:
    t = db.get(Ticket, ticket_id)
    if not t:
        raise HTTPException(404, 'Ticket not found')
    return t


@router.get('/flags', dependencies=[staff])
def get_flags():
    return flags.all_flags()


@router.get('/tickets', dependencies=[staff])
def list_tickets(db: Session = Depends(get_db)):
    rows = db.scalars(select(Ticket)).all()
    rows.sort(key=lambda t: (SEV_RANK.get(t.severity, 0), t.created_at), reverse=True)
    return [_summary(db, t) for t in rows]


@router.patch('/tickets/{ticket_id}')
def patch_ticket(ticket_id: str, body: TicketPatch, user=staff, db: Session = Depends(get_db)):
    t, actor = _get(db, ticket_id), f"user:{user['sub']}"
    if body.category:
        tickets.add_event(db, t.id, 'category_corrected', {'from': t.category, 'to': body.category}, actor)
        t.category, t.needs_human_review = body.category, False
    if body.department_id:
        dept = db.get(Department, body.department_id)
        if not dept:
            raise HTTPException(404, 'Department not found')
        from services.admin.categorization import get_or_create_admin
        row = get_or_create_admin(db, t)
        row.department_id, row.assigned_by = dept.id, actor
        row.municipal_category = (dept.categories or [None])[0]
        tickets.add_event(db, t.id, 'department_assigned', {'department': dept.name}, actor)
        queue.dequeue(db, t.id)
    db.commit()
    if body.status:
        try:
            tickets.transition(db, t, body.status, actor)
        except tickets.InvalidTransition as e:
            raise HTTPException(409, str(e))
    return _summary(db, t)


@router.get('/queue/unclassified', dependencies=[staff])
def unclassified_queue(db: Session = Depends(get_db)):
    rows = db.execute(select(UnclassifiedQueue, Ticket).join(Ticket, Ticket.id == UnclassifiedQueue.ticket_id)
                      .order_by(UnclassifiedQueue.queued_at)).all()
    return [{'ticket_id': t.id, 'public_ref': t.public_ref, 'reason': q.reason, 'retry_count': q.retry_count,
             'queued_at': iso(q.queued_at)} for q, t in rows]


@router.post('/tickets/{ticket_id}/reprocess', dependencies=[staff])
def reprocess(ticket_id: str, request: Request, db: Session = Depends(get_db)):
    t = _get(db, ticket_id)
    pipeline.run_enrichment(request.app.state.session_factory, t.id)
    db.expire_all()
    return _summary(db, db.get(Ticket, t.id))
