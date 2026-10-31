from PIL import Image

from config import settings
from tests.conftest import make_jpeg, post_report


def test_valid_report_creates_a_ticket(client):
    r = post_report(client)
    assert r.status_code == 201
    ref = r.json()['public_ref']
    assert ref.startswith('INF-')
    assert client.get(f'/api/tickets/{ref}').status_code == 200


def test_rejects_a_file_that_is_not_an_image(client):
    r = client.post('/api/reports', files={'image': ('x.jpg', b'not an image', 'image/jpeg')}, data={'lat': 1, 'lng': 1})
    assert r.status_code == 422
    assert r.json()['detail']['code'] == 'invalid_image'


def test_rejects_missing_location(client):
    r = post_report(client, lat=None, lng=None)
    assert r.status_code == 422
    assert r.json()['detail']['code'] == 'missing_location'


def test_rejects_impossible_location(client):
    assert post_report(client, lat=999).json()['detail']['code'] == 'invalid_location'


def test_low_resolution_is_flagged_not_rejected(client):
    r = post_report(client, image=make_jpeg(size=(100, 100)))
    assert r.status_code == 201
    assert 'low_resolution' in r.json()['quality_flags']


def test_exif_metadata_is_stripped_from_stored_photo(client):
    assert post_report(client, image=make_jpeg(exif=True)).status_code == 201
    stored = next(settings.upload_dir().iterdir())
    assert len(Image.open(stored).getexif()) == 0


def test_same_photo_twice_returns_the_same_ticket(client):
    img = make_jpeg()
    first = post_report(client, image=img).json()
    second = post_report(client, image=img)
    assert second.status_code == 200
    assert second.json()['duplicate'] is True
    assert second.json()['public_ref'] == first['public_ref']
