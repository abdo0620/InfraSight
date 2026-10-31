import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import adapters.jurisdiction as jurisdiction_adapter
import adapters.utilities as utilities_adapter
import adapters.zoning as zoning_adapter
from adapters.base import AdapterError
from config import feature_flags
from db.database import make_engine
from db.seeds.seed import create_staff_user
from main import create_app
from services.ai import muse_spark

PARIS = (48.8566, 2.3522)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    monkeypatch.setenv('UPLOAD_DIR', str(tmp_path / 'uploads'))
    monkeypatch.setenv('ENRICHMENT_BACKOFF_S', '0')
    monkeypatch.setenv('SECRET_KEY', 'test-secret')
    monkeypatch.setenv('AI_MOCK', '1')
    for name in feature_flags.DEFAULTS:
        monkeypatch.delenv('FLAG_' + name.upper(), raising=False)


@pytest.fixture
def app():
    return create_app(engine=make_engine('sqlite://'))


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def db(app):
    with app.state.session_factory() as session:
        yield session


@pytest.fixture
def set_flags(monkeypatch):
    def _set(**kw):
        for name, value in kw.items():
            monkeypatch.setenv('FLAG_' + name.upper(), '1' if value else '0')
    return _set


@pytest.fixture
def staff(client, app):
    with app.state.session_factory() as s:
        create_staff_user(s, 'admin', 'pw-test')
    token = client.post('/api/auth/login', json={'username': 'admin', 'password': 'pw-test'}).json()['token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def fake_assess(monkeypatch):
    """Control what the 'model' says: fake_assess('pothole', 8)."""
    def _set(category='pothole', score=5, confidence=0.9):
        bucket = 'low' if score <= 3 else 'medium' if score <= 6 else 'high'
        monkeypatch.setattr(muse_spark, 'assess_damage', lambda *a, **k: {
            'category': category, 'severity_score': score, 'severity': bucket, 'confidence': confidence,
            'uncertainties': [], 'source': 'test'})
    return _set


@pytest.fixture
def kill_adapters(monkeypatch):
    def boom():
        raise AdapterError('provider down')
    for module in (jurisdiction_adapter, zoning_adapter, utilities_adapter):
        monkeypatch.setattr(module, 'get_provider', boom)


def make_jpeg(size=(640, 480), color=(120, 120, 120), exif=False) -> bytes:
    img = Image.new('RGB', size, color)
    buf = io.BytesIO()
    if exif:
        data = Image.Exif()
        data[0x010F] = 'SecretCameraMaker'
        img.save(buf, 'JPEG', exif=data)
    else:
        img.save(buf, 'JPEG')
    return buf.getvalue()


def post_report(client, image=None, lat=PARIS[0], lng=PARIS[1], description='', filename='p.jpg'):
    files = {'image': (filename, image if image is not None else make_jpeg(), 'image/jpeg')}
    data = {'description': description}
    if lat is not None:
        data['lat'] = lat
    if lng is not None:
        data['lng'] = lng
    return client.post('/api/reports', files=files, data=data)
