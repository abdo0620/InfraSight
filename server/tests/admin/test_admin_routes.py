from sqlalchemy import select

from db.models import Department, Ticket
from services.security import create_token
from tests.conftest import make_jpeg, post_report


def test_admin_requires_a_token(client):
    assert client.get('/api/admin/tickets').status_code == 401


def test_admin_rejects_the_wrong_role(client):
    h = {'Authorization': 'Bearer ' + create_token('x', 'citizen')}
    assert client.get('/api/admin/tickets', headers=h).status_code == 403


def test_list_is_sorted_most_severe_first(client, staff, fake_assess):
    fake_assess('pothole', 2)
    post_report(client, image=make_jpeg(color=(1, 1, 1)))
    fake_assess('pothole', 9)
    post_report(client, image=make_jpeg(color=(2, 2, 2)))
    rows = client.get('/api/admin/tickets', headers=staff).json()
    assert [r['severity'] for r in rows] == ['high', 'low']
    assert rows[0]['compliance_label'] == '2'


def test_invalid_status_change_is_409_and_valid_one_works(client, staff, db, fake_assess):
    fake_assess('pothole', 5)
    post_report(client)
    tid = db.scalar(select(Ticket)).id
    assert client.patch(f'/api/admin/tickets/{tid}', json={'status': 'resolved'}, headers=staff).status_code == 409
    r = client.patch(f'/api/admin/tickets/{tid}', json={'status': 'triaged'}, headers=staff)
    assert r.status_code == 200 and r.json()['status'] == 'triaged'


def test_manual_department_assignment_clears_the_queue(client, staff, db, set_flags):
    set_flags(ai_assessment_enabled=False)
    post_report(client)
    assert len(client.get('/api/admin/queue/unclassified', headers=staff).json()) == 1
    tid = db.scalar(select(Ticket)).id
    dept = db.scalar(select(Department).where(Department.name == 'Parks & Green Spaces'))
    client.patch(f'/api/admin/tickets/{tid}', json={'department_id': dept.id}, headers=staff)
    assert client.get('/api/admin/queue/unclassified', headers=staff).json() == []


def test_reprocess_recovers_a_failed_ticket(client, staff, db, set_flags):
    set_flags(ai_assessment_enabled=False)
    post_report(client)
    tid = db.scalar(select(Ticket)).id
    assert client.get('/api/admin/queue/unclassified', headers=staff).json()
    client.patch(f'/api/admin/tickets/{tid}', json={'category': 'pothole'}, headers=staff)
    r = client.post(f'/api/admin/tickets/{tid}/reprocess', headers=staff)
    assert r.status_code == 200 and r.json()['department'] == 'Road Maintenance'
    assert client.get('/api/admin/queue/unclassified', headers=staff).json() == []


def test_flags_endpoint(client, staff):
    flags = client.get('/api/admin/flags', headers=staff).json()
    assert flags['tier3_compliance_enabled'] is False and flags['tier2_admin_enabled'] is True
