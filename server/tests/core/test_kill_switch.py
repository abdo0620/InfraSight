"""THE guarantee: Tier 1 works with every flag off and every adapter dead."""
from sqlalchemy import select

from db.models import Ticket, TicketAdmin, TicketCompliance, UnclassifiedQueue
from db.models.core import TicketFallback
from services.ai import muse_spark
from tests.conftest import post_report


def test_tier1_works_with_all_flags_off_and_adapters_dead(client, db, set_flags, kill_adapters):
    set_flags(tier2_admin_enabled=False, tier3_compliance_enabled=False, tier3_utility_alerts_enabled=False,
              tier3_sop_generation_enabled=False, ai_assessment_enabled=False)
    r = post_report(client)
    assert r.status_code == 201
    body = r.json()
    assert (body['category'], body['severity'], body['needs_human_review']) == ('uncategorized', 'unknown', True)
    assert client.get(f"/api/tickets/{body['public_ref']}").status_code == 200

    db.expire_all()
    t = db.scalar(select(Ticket))
    assert t.compliance_level == 1
    assert db.get(TicketAdmin, t.id) is None and db.get(TicketCompliance, t.id) is None


def test_tier1_works_with_flags_on_but_model_and_adapters_failing(client, db, set_flags, kill_adapters, monkeypatch):
    set_flags(tier2_admin_enabled=True, tier3_compliance_enabled=True)

    def broken(*a, **k):
        raise RuntimeError('model down')
    monkeypatch.setattr(muse_spark, 'assess_damage', broken)

    r = post_report(client)
    assert r.status_code == 201
    assert client.get(f"/api/tickets/{r.json()['public_ref']}").status_code == 200

    db.expire_all()
    t = db.scalar(select(Ticket))
    assert t.category == 'uncategorized' and t.needs_human_review
    assert t.compliance_level == 2                       # tier 2 still applied (default SLA)
    assert db.scalar(select(UnclassifiedQueue)) is not None
    steps = {f.step for f in db.scalars(select(TicketFallback)).all()}
    assert {'dept_categorization', 'jurisdiction_lookup'} <= steps
