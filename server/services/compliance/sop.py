"""Tier 3: SOP + traffic management drafts. Always drafts: human_approved starts False."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models.compliance import TicketPermitCheck, TicketSopDocument
from db.models.core import Ticket
from services.ai import muse_spark

KINDS = ('public_works_sop', 'traffic_management_plan')


def generate(db: Session, ticket: Ticket, kinds=KINDS) -> dict:
    permits = [p.permit_type for p in db.scalars(select(TicketPermitCheck).where(TicketPermitCheck.ticket_id == ticket.id)).all()]
    ctx = {'public_ref': ticket.public_ref, 'category': ticket.category, 'severity': ticket.severity,
           'lat': ticket.lat, 'lng': ticket.lng, 'permits': permits}
    ids = []
    for kind in kinds:
        content = muse_spark.draft_sop(ctx, kind)
        version = (db.scalar(select(func.max(TicketSopDocument.version)).where(
            TicketSopDocument.ticket_id == ticket.id, TicketSopDocument.kind == kind)) or 0) + 1
        doc = TicketSopDocument(ticket_id=ticket.id, kind=kind, content=content, version=version,
                                ai_generated=True, human_approved=False)
        db.add(doc)
        db.flush()
        ids.append(doc.id)
    return {'documents': ids}


def approve(db: Session, doc_id: str, approver: str) -> TicketSopDocument:
    doc = db.get(TicketSopDocument, doc_id)
    if not doc:
        raise KeyError(doc_id)
    doc.human_approved, doc.approved_by = True, approver
    db.commit()
    return doc
