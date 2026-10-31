"""Tier 2: the Unclassified_Municipal_Queue worklist."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.admin import UnclassifiedQueue


def enqueue(db: Session, ticket_id: str, reason: str) -> UnclassifiedQueue:
    row = db.scalar(select(UnclassifiedQueue).where(UnclassifiedQueue.ticket_id == ticket_id))
    if row:
        row.reason, row.retry_count = reason, row.retry_count + 1
    else:
        row = UnclassifiedQueue(ticket_id=ticket_id, reason=reason)
        db.add(row)
    db.commit()
    return row


def dequeue(db: Session, ticket_id: str) -> None:
    row = db.scalar(select(UnclassifiedQueue).where(UnclassifiedQueue.ticket_id == ticket_id))
    if row:
        db.delete(row)
        db.commit()
