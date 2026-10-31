"""Notifications. v1 records an audit event; plug email/SMS/push here. Never raises."""
import logging

from sqlalchemy.orm import Session

from services.core.tickets import add_event

log = logging.getLogger(__name__)


def notify(db: Session, ticket_id: str, audience: str, message: str) -> None:
    try:
        add_event(db, ticket_id, 'notification', {'audience': audience, 'message': message}, 'service:notifications')
        db.commit()
        log.info('notify[%s] %s: %s', audience, ticket_id, message)
    except Exception:  # noqa: BLE001  (a failed notification never affects the ticket)
        db.rollback()
        log.exception('notification failed')
