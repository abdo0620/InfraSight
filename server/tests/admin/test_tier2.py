from datetime import timedelta

from sqlalchemy import delete, select

from db.models import Department, SlaPolicy, Ticket, TicketAdmin, UnclassifiedQueue
from db.models.core import TicketFallback
from tests.conftest import post_report


def _row(db):
    db.expire_all()
    t = db.scalar(select(Ticket))
    return t, db.get(TicketAdmin, t.id)


def test_pothole_gets_department_and_urgent_sla(client, db, fake_assess):
    fake_assess('pothole', 8)
    post_report(client)
    t, admin = _row(db)
    assert db.get(Department, admin.department_id).name == 'Road Maintenance'
    assert db.get(SlaPolicy, admin.sla_policy_id).name == 'urgent-48h'
    assert admin.sla_due_at - t.created_at == timedelta(days=2)
    assert t.compliance_level == 2


def test_low_severity_uses_the_low_policy(client, db, fake_assess):
    fake_assess('pothole', 2)
    post_report(client)
    _, admin = _row(db)
    assert db.get(SlaPolicy, admin.sla_policy_id).name == 'non-urgent-7d'


def test_category_specific_policy_wins(client, db, fake_assess):
    fake_assess('street_lighting', 5)
    post_report(client)
    _, admin = _row(db)
    assert db.get(SlaPolicy, admin.sla_policy_id).name == 'lighting-5d'


def test_uncategorized_goes_to_queue_with_default_sla(client, db, set_flags):
    set_flags(ai_assessment_enabled=False)
    post_report(client)
    t, admin = _row(db)
    assert admin.department_id is None
    assert db.get(SlaPolicy, admin.sla_policy_id).is_default
    assert db.scalar(select(UnclassifiedQueue)).reason == 'dept_mapping_failed'


def test_empty_policy_table_falls_back_to_builtin_default(client, db, fake_assess):
    fake_assess('pothole', 5)
    db.execute(delete(SlaPolicy))
    db.commit()
    post_report(client)
    t, admin = _row(db)
    assert admin.sla_policy_id is None
    assert admin.sla_due_at - t.created_at == timedelta(days=7)
    assert 'no_policy_found' in {f.reason for f in db.scalars(select(TicketFallback)).all()}


def test_tier2_flag_off_leaves_level_1_and_logs_it(client, db, set_flags):
    set_flags(tier2_admin_enabled=False)
    post_report(client)
    t, admin = _row(db)
    assert admin is None and t.compliance_level == 1
    assert any(f.reason == 'flag_disabled' and f.tier == 2 for f in db.scalars(select(TicketFallback)).all())
