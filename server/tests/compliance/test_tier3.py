from sqlalchemy import select

from db.models import (Ticket, TicketCompliance, TicketPermitCheck, TicketSopDocument, TicketUtilityAlert,
                       UnclassifiedQueue)
from db.models.core import TicketFallback
from tests.conftest import post_report

import adapters.utilities as utilities_adapter


def _state(db):
    db.expire_all()
    t = db.scalar(select(Ticket))
    return t, db.get(TicketCompliance, t.id)


def test_happy_path_reaches_level_3(client, db, set_flags, fake_assess):
    set_flags(tier3_compliance_enabled=True)
    fake_assess('pothole', 5)
    post_report(client)
    t, comp = _state(db)
    assert t.compliance_level == 3 and comp.status == 'complete'
    assert {p.permit_type for p in db.scalars(select(TicketPermitCheck)).all()} == {'dt_dict', 'permission_voirie'}
    alert = db.scalar(select(TicketUtilityAlert))
    assert alert.status == 'sent' and alert.alert_ref.startswith('SIM-')   # sandbox: simulated, nothing real is sent
    sops = db.scalars(select(TicketSopDocument)).all()
    assert len(sops) == 2 and not any(d.human_approved for d in sops)


def test_rules_decide_which_permits_apply(client, db, set_flags, fake_assess):
    set_flags(tier3_compliance_enabled=True)
    fake_assess('street_furniture', 5)
    post_report(client)
    assert {p.permit_type for p in db.scalars(select(TicketPermitCheck)).all()} == {'permission_voirie'}
    assert db.scalar(select(TicketUtilityAlert)) is None           # not required for this category


def test_location_outside_any_jurisdiction_goes_to_the_queue(client, db, set_flags, fake_assess):
    set_flags(tier3_compliance_enabled=True)
    fake_assess('pothole', 5)
    post_report(client, lat=40.7, lng=-74.0)
    t, comp = _state(db)
    assert t.compliance_level == 2 and comp.status == 'degraded'
    assert 'jurisdiction_lookup_failed' in db.scalar(select(UnclassifiedQueue)).reason
    assert any(f.step == 'jurisdiction_lookup' and f.reason == 'no_match' for f in db.scalars(select(TicketFallback)).all())


def test_utility_timeout_is_retried_then_degraded(client, db, set_flags, fake_assess, monkeypatch):
    set_flags(tier3_compliance_enabled=True)
    fake_assess('pothole', 5)
    calls = []

    class Slow:
        def submit_alert(self, **kw):
            calls.append(1)
            raise TimeoutError('operator network timeout')
    monkeypatch.setattr(utilities_adapter, 'get_provider', lambda: Slow())
    r = post_report(client)
    assert r.status_code == 201
    t, comp = _state(db)
    assert len(calls) == 3                                           # bounded retries
    assert t.compliance_level == 3 and comp.status == 'degraded'     # "3-DEGRADED"
    assert db.scalar(select(TicketUtilityAlert)).status == 'failed'
    assert any(f.reason == 'provider_timeout' for f in db.scalars(select(TicketFallback)).all())


def test_sub_flag_skips_only_that_step(client, db, set_flags, fake_assess):
    set_flags(tier3_compliance_enabled=True, tier3_utility_alerts_enabled=False)
    fake_assess('pothole', 5)
    post_report(client)
    _, comp = _state(db)
    assert comp.status == 'complete'
    assert db.scalar(select(TicketUtilityAlert)) is None
    assert any(f.step == 'utility_alert' and f.reason == 'flag_disabled' for f in db.scalars(select(TicketFallback)).all())


def test_routes_return_501_when_tier3_is_off(client):
    assert client.get('/api/compliance/tickets/anything').status_code == 501


def test_routes_need_staff_when_tier3_is_on(client, set_flags):
    set_flags(tier3_compliance_enabled=True)
    assert client.get('/api/compliance/tickets/anything').status_code == 401


def test_compliance_status_and_sop_approval(client, db, staff, set_flags, fake_assess):
    set_flags(tier3_compliance_enabled=True)
    fake_assess('pothole', 5)
    post_report(client)
    tid = db.scalar(select(Ticket)).id
    body = client.get(f'/api/compliance/tickets/{tid}', headers=staff).json()
    assert body['status'] == 'complete' and body['jurisdiction'] == 'fr-paris' and len(body['sop_documents']) == 2
    doc_id = body['sop_documents'][0]['id']
    assert client.post(f'/api/compliance/sop/{doc_id}/approve', headers=staff).json()['human_approved'] is True


def test_reprocess_is_idempotent(client, db, staff, set_flags, fake_assess):
    set_flags(tier3_compliance_enabled=True)
    fake_assess('pothole', 5)
    post_report(client)
    tid = db.scalar(select(Ticket)).id
    client.post(f'/api/admin/tickets/{tid}/reprocess', headers=staff)
    db.expire_all()
    assert len(db.scalars(select(TicketPermitCheck)).all()) == 2          # no duplicates
    assert len(db.scalars(select(TicketUtilityAlert)).all()) == 1
