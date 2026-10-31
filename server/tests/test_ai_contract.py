"""The client <-> server contract from docs/API.md."""
import base64
import io
import json

from PIL import Image

from tests.conftest import make_jpeg


def _decode(data_url: str) -> Image.Image:
    return Image.open(io.BytesIO(base64.b64decode(data_url.split(',', 1)[1])))


def _mask(client):
    r = client.post('/api/segment', files={'image': ('p.jpg', make_jpeg(), 'image/jpeg')}, data={'point': json.dumps({'x': .5, 'y': .5})})
    assert r.status_code == 200
    return r.json()['mask']


def test_segment_returns_a_transparent_png_mask(client):
    mask = _decode(_mask(client))
    assert mask.mode == 'RGBA' and mask.size == (640, 480)
    alpha = mask.split()[3]
    assert alpha.getpixel((320, 240)) == 255 and alpha.getpixel((2, 2)) == 0


def test_segment_validates_the_point(client):
    r = client.post('/api/segment', files={'image': ('p.jpg', make_jpeg(), 'image/jpeg')}, data={'point': '{"x": 5}'})
    assert r.status_code == 422


def test_assess_returns_the_documented_fields(client):
    r = client.post('/api/assess', files={'image': ('p.jpg', make_jpeg(), 'image/jpeg')})
    body = r.json()
    assert set(body) == {'damage_type', 'severity', 'tripping_hazard', 'exposed_materials', 'accessibility_impact', 'recommended_action', 'priority'}
    assert 1 <= body['severity'] <= 10 and body['priority'] in ('Low', 'Standard', 'Urgent')


def test_repair_returns_a_jpeg_data_url(client):
    mask_bytes = base64.b64decode(_mask(client).split(',', 1)[1])
    r = client.post('/api/repair', files={'image': ('p.jpg', make_jpeg(), 'image/jpeg'), 'mask': ('m.png', mask_bytes, 'image/png')})
    assert r.json()['image'].startswith('data:image/jpeg;base64,')
    assert _decode(r.json()['image']).size == (640, 480)


def test_real_models_not_wired_returns_501(client, monkeypatch):
    monkeypatch.setenv('AI_MOCK', '0')
    r = client.post('/api/assess', files={'image': ('p.jpg', make_jpeg(), 'image/jpeg')})
    assert r.status_code == 501
