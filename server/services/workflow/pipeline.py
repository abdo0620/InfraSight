"""Enrichment orchestrator: runs Tier 2 then Tier 3 AFTER the ticket exists.

Contract: no step can block or fail the ticket. Each step is attempted a bounded number of times;
on final failure the fallback is recorded in ticket_fallbacks + ticket_events and the pipeline moves on.
Every step is idempotent (upserts), so an ops user can safely reprocess a ticket.
"""
import logging
import time
from dataclasses import dataclass

from config import feature_flags as flags
from config import settings
from db.models.compliance import TicketCompliance
from db.models.core import Ticket, TicketFallback
from services.admin import categorization, queue, sla
from services.compliance import jurisdiction, permits, sop, utilities
from services.core.errors import NoMatch
from services.core.tickets import add_event
from services.notifications import notify

log = logging.getLogger(__name__)


@dataclass
class StepResult:
    ok: bool
    data: dict | None = None
    reason: str | None = None
    fallback: str | None = None


def _log_fallback(db, ticket, tier, step, reason, fallback, detail=None):
    db.add(TicketFallback(ticket_id=ticket.id, tier=tier, step=step, reason=reason, fallback=fallback, detail=detail))
    add_event(db, ticket.id, 'fallback', {'tier': tier, 'step': step, 'reason': reason, 'fallback': fallback}, 'service:workflow')
    db.commit()


def _step(db, ticket, *, tier, step, fn, fallback, on_failure=None) -> StepResult:
    retries, last, reason, attempts = settings.enrichment_retries(), None, 'provider_error', 0
    for attempt in range(1, retries + 1):
        attempts = attempt
        try:
            data = fn(db, ticket) or {}
            add_event(db, ticket.id, 'compliance_attempt', {'step': step, 'tier': tier, 'ok': True, 'attempts': attempts}, 'service:workflow')
            db.commit()
            if data.get('fallback_reason'):  # step succeeded but had to use a default
                _log_fallback(db, ticket, tier, step, data['fallback_reason'], fallback)
            return StepResult(True, data)
        except NoMatch as exc:  # deterministic: retrying cannot help
            db.rollback()
            last, reason = exc, 'no_match'
            break
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            last = exc
            reason = 'provider_timeout' if isinstance(exc, TimeoutError) else 'provider_error'
            if attempt < retries:
                time.sleep(settings.enrichment_backoff_s() * 2 ** (attempt - 1))
    if on_failure:
        try:
            on_failure(db, ticket, last)
        except Exception:  # noqa: BLE001
            db.rollback()
    add_event(db, ticket.id, 'compliance_attempt', {'step': step, 'tier': tier, 'ok': False, 'attempts': attempts}, 'service:workflow')
    _log_fallback(db, ticket, tier, step, reason, fallback, {'error': f'{type(last).__name__}: {last}', 'attempts': attempts})
    return StepResult(False, reason=reason, fallback=fallback)


def _run(db, ticket_id: str) -> None:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        return
    level, queue_reasons = 1, []

    # ---- Tier 2: basic administrative layer ----
    if flags.is_enabled('tier2_admin_enabled'):
        if not _step(db, ticket, tier=2, step='dept_categorization', fn=categorization.map_department, fallback='unassigned').ok:
            queue_reasons.append('dept_mapping_failed')
        _step(db, ticket, tier=2, step='sla_assignment', fn=sla.assign_sla, fallback='default_sla', on_failure=sla.apply_default)
        level = 2
    else:
        _log_fallback(db, ticket, 2, 'tier2_pipeline', 'flag_disabled', 'skipped')

    # ---- Tier 3: advanced regulatory layer ----
    if flags.is_enabled('tier3_compliance_enabled'):
        comp = jurisdiction.get_or_create_compliance(db, ticket)
        comp.status = 'in_progress'
        db.commit()
        if not _step(db, ticket, tier=3, step='jurisdiction_lookup', fn=jurisdiction.resolve, fallback='unclassified_queue').ok:
            queue_reasons.append('jurisdiction_lookup_failed')
            db.get(TicketCompliance, ticket.id).status = 'degraded'  # nothing further can apply
            db.commit()
        else:
            degraded = not _step(db, ticket, tier=3, step='permit_checklist', fn=permits.build_checklist, fallback='empty_checklist').ok
            if flags.tier3_utility_alerts():
                degraded |= not _step(db, ticket, tier=3, step='utility_alert', fn=utilities.submit_alert,
                                      fallback='alert_failed', on_failure=utilities.record_failure).ok
            else:
                _log_fallback(db, ticket, 3, 'utility_alert', 'flag_disabled', 'skipped')
            if flags.tier3_sop():
                degraded |= not _step(db, ticket, tier=3, step='sop_generation', fn=sop.generate, fallback='no_sop').ok
            else:
                _log_fallback(db, ticket, 3, 'sop_generation', 'flag_disabled', 'skipped')
            db.get(TicketCompliance, ticket.id).status = 'degraded' if degraded else 'complete'
            db.commit()
            level = 3
    else:
        _log_fallback(db, ticket, 3, 'tier3_pipeline', 'flag_disabled', 'skipped')

    # ---- worklist + final level (never regresses) ----
    if queue_reasons:
        queue.enqueue(db, ticket.id, ','.join(queue_reasons))
    else:
        queue.dequeue(db, ticket.id)
    ticket.compliance_level = max(ticket.compliance_level, level)
    db.commit()
    notify(db, ticket.id, 'municipal', f'Enrichment finished at level {ticket.compliance_level}')


def run_enrichment(session_factory, ticket_id: str) -> None:
    """Entry point for background tasks and reprocessing. Never raises."""
    with session_factory() as db:
        try:
            _run(db, ticket_id)
        except Exception:  # noqa: BLE001
            db.rollback()
            log.exception('enrichment crashed for %s (ticket is unaffected)', ticket_id)
