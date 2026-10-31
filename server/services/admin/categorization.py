"""Tier 2: map the AI category to a municipal category and department."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.admin import Department, TicketAdmin
from db.models.core import Ticket
from services.core.errors import NoMatch

CATEGORY_TO_MUNICIPAL = {
    'pothole': 'roadwork', 'sidewalk_damage': 'roadwork', 'street_furniture': 'street_furniture',
    'street_lighting': 'street_lighting', 'vegetation': 'parks',
}


def get_or_create_admin(db: Session, ticket: Ticket) -> TicketAdmin:
    row = db.get(TicketAdmin, ticket.id)
    if not row:
        row = TicketAdmin(ticket_id=ticket.id)
        db.add(row)
    return row


def map_department(db: Session, ticket: Ticket) -> dict:
    municipal = CATEGORY_TO_MUNICIPAL.get(ticket.category)
    if not municipal:
        raise NoMatch(f'no municipal category for "{ticket.category}"')
    dept = next((d for d in db.scalars(select(Department).where(Department.is_active.is_(True))).all()
                 if municipal in (d.categories or [])), None)
    if not dept:
        raise NoMatch(f'no active department accepts "{municipal}"')
    row = get_or_create_admin(db, ticket)
    row.municipal_category, row.department_id = municipal, dept.id
    row.assigned_by, row.assigned_at = 'system:categorization', datetime.now(timezone.utc)
    return {'municipal_category': municipal, 'department': dept.name}
