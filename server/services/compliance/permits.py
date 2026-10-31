"""Tier 3: build the permit checklist from versioned rule data (compliance-rules/permit-checklists)."""
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from db.models.compliance import TicketPermitCheck
from db.models.core import Ticket
from services.compliance.jurisdiction import jurisdiction_for
from services.core.errors import NoMatch

ORDER = {'low': 1, 'medium': 2, 'high': 3}


def _applies(permit: dict, ticket: Ticket) -> bool:
    rule = permit.get('applies_to', {})
    if rule.get('categories') and ticket.category not in rule['categories']:
        return False
    # unknown severity is treated conservatively: the permit applies
    need = ORDER.get(rule.get('min_severity', 'low'), 1)
    return ticket.severity not in ORDER or ORDER[ticket.severity] >= need


def build_checklist(db: Session, ticket: Ticket) -> dict:
    j = jurisdiction_for(db, ticket)
    path = settings.RULES_DIR / 'permit-checklists' / f'{j.code}.json'
    if not path.exists():
        raise NoMatch(f'no permit rules for {j.code}')
    rules = json.loads(path.read_text(encoding='utf-8'))
    created = 0
    for p in rules['permits']:
        if not _applies(p, ticket):
            continue
        row = db.scalar(select(TicketPermitCheck).where(
            TicketPermitCheck.ticket_id == ticket.id, TicketPermitCheck.permit_type == p['permit_type']))
        if row is None:  # idempotent: never overwrite progress on an existing check
            db.add(TicketPermitCheck(ticket_id=ticket.id, permit_type=p['permit_type'], requirement=p['requirement'],
                                     checklist=p['checklist'], source_rule=f"{p['id']}@v{rules['version']}"))
            created += 1
    return {'permits_created': created}
