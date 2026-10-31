"""Model endpoints used by the client when AI.useMock=false (contract: docs/API.md)."""
import base64
import json

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import UnidentifiedImageError

from services.ai import muse_image, muse_spark, sam
from services.ai.errors import ModelNotConfigured

router = APIRouter(prefix='/api', tags=['ai'])


def _data_url(data: bytes, mime: str) -> str:
    return f'data:{mime};base64,{base64.b64encode(data).decode()}'


def _run(fn):
    try:
        return fn()
    except ModelNotConfigured as e:
        raise HTTPException(501, str(e))
    except (UnidentifiedImageError, OSError):
        raise HTTPException(422, 'Unreadable image')


@router.post('/segment')
def segment(image: UploadFile = File(...), point: str = Form(...)):
    try:
        p = json.loads(point)
        x, y = float(p['x']), float(p['y'])
        assert 0 <= x <= 1 and 0 <= y <= 1
    except (ValueError, KeyError, TypeError, AssertionError):
        raise HTTPException(422, 'point must be {"x":0..1,"y":0..1}')
    return {'mask': _data_url(_run(lambda: sam.segment(image.file.read(), x, y)), 'image/png')}


@router.post('/assess')
def assess(image: UploadFile = File(...), mask: UploadFile | None = File(None)):
    raw = _run(lambda: muse_spark.assess_damage(image.file.read(), mask.file.read() if mask else None))
    keys = ('damage_type', 'tripping_hazard', 'exposed_materials', 'accessibility_impact', 'recommended_action', 'priority')
    return {**{k: raw[k] for k in keys}, 'severity': raw['severity_score']}


@router.post('/repair')
def repair(image: UploadFile = File(...), mask: UploadFile = File(...)):
    return {'image': _data_url(_run(lambda: muse_image.repair(image.file.read(), mask.file.read())), 'image/jpeg')}
