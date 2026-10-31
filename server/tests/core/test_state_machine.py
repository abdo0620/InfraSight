import pytest

from services.core import tickets


def _ticket(db):
    return tickets.create_ticket(db, lat=1, lng=1, description='', category='pothole', severity='low',
                                 photo_asset_id=None, needs_human_review=False)


def test_valid_path(db):
    t = _ticket(db)
    for status in ('triaged', 'scheduled', 'in_progress', 'resolved'):
        tickets.transition(db, t, status, 'user:test')
    assert t.status == 'resolved'


def test_invalid_transition_is_refused(db):
    t = _ticket(db)
    with pytest.raises(tickets.InvalidTransition):
        tickets.transition(db, t, 'resolved', 'user:test')


def test_refs_are_unique_and_sequential(db):
    a, b = _ticket(db), _ticket(db)
    assert a.public_ref != b.public_ref
