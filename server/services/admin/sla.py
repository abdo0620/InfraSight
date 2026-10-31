"""Tier 2: pick the most specific SLA policy, else the default."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models.admin import SlaPolicy
from db.models.core import Ticket
from services.admin.categorization import get_or_create_admin

FALLBACK_RESPONSE_DAYS = 7  # used only when the policy table is empty or broken


def _matches(pattern: str | None, value: str) -> bool | None:
    """None = pattern absent (neutral); True/False = matched or not."""
    if not pattern:
        return None
    return pattern == '*' or value in [p.strip() for p in pattern.split(',')]


def _score(policy: SlaPolicy, ticket: Ticket) -> int:
    parts = [_matches(policy.category_pattern, ticket.category), _matches(policy.severity_pattern, ticket.severity)]
    if any(p is False for p in parts):
        return -1
    return sum(1 for p in parts if p)


def _anchor(ticket: Ticket) -> datetime:
    t = ticket.created_at
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def assign_sla(db: Session, ticket: Ticket) -> dict:
    policies = db.scalars(select(SlaPolicy).where(SlaPolicy.active.is_(True))).all()
    specific = [p for p in policies if not p.is_default and _score(p, ticket) > 0]
    chosen = max(specific, key=lambda p: (_score(p, ticket), -p.response_days), default=None) \
        or next((p for p in policies if p.is_default), None)
    if chosen is None:
        return apply_default(db, ticket, reason='no_policy_found')
    row = get_or_create_admin(db, ticket)
    row.sla_policy_id = chosen.id
    row.sla_due_at = _anchor(ticket) + timedelta(days=chosen.response_days)
    return {'policy': chosen.name, 'response_days': chosen.response_days}


def apply_default(db: Session, ticket: Ticket, exc: Exception | None = None, reason: str = 'sla_error') -> dict:
    """Fallback: hard default so a ticket always has a due date."""
    row = get_or_create_admin(db, ticket)
    row.sla_policy_id = None
    row.sla_due_at = _anchor(ticket) + timedelta(days=FALLBACK_RESPONSE_DAYS)
    db.commit()
    return {'policy': 'builtin-default', 'response_days': FALLBACK_RESPONSE_DAYS, 'fallback_reason': reason}
