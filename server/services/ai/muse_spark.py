"""Muse Spark client: structural diagnostics and SOP drafting.
Mock mode is deterministic (derived from the image hash) and clearly labelled as such."""
import hashlib

from config import settings
from services.ai.errors import ModelNotConfigured

CATEGORIES = ['pothole', 'sidewalk_damage', 'street_furniture', 'street_lighting', 'vegetation']
DAMAGE_LABEL = {
    'pothole': 'Road surface damage', 'sidewalk_damage': 'Sidewalk damage',
    'street_furniture': 'Street furniture damage', 'street_lighting': 'Street lighting fault',
    'vegetation': 'Vegetation obstruction', 'other': 'Other damage',
}


def _bucket(score: int) -> str:
    return 'low' if score <= 3 else 'medium' if score <= 6 else 'high'


def assess_damage(image_bytes: bytes, mask_bytes: bytes | None = None) -> dict:
    """Return the rich assessment used by both the ticket pipeline and /api/assess."""
    if not settings.ai_mock():
        raise ModelNotConfigured('Wire Muse Spark in services/ai/muse_spark.py')
    h = hashlib.sha256(image_bytes).digest()
    category = CATEGORIES[h[0] % len(CATEGORIES)]
    score = 2 + h[1] % 8  # 2..9
    bucket = _bucket(score)
    return {
        'category': category,
        'severity_score': score,
        'severity': bucket,
        'confidence': round(0.55 + (h[2] % 40) / 100, 2),
        'uncertainties': ['Mock model: placeholder result, not a real assessment'],
        'damage_type': DAMAGE_LABEL[category],
        'tripping_hazard': {'low': 'Low', 'medium': 'Moderate', 'high': 'High'}[bucket],
        'exposed_materials': ['Gravel base', 'Aggregate'] if category in ('pothole', 'sidewalk_damage') else [],
        'accessibility_impact': 'Blocks wheelchair and stroller passage' if score >= 6 else 'Uneven surface, minor obstruction',
        'recommended_action': {'high': 'Cordon off and repair within 48 hours',
                               'medium': 'Schedule repair within 2 weeks',
                               'low': 'Add to routine maintenance'}[bucket],
        'priority': {'high': 'Urgent', 'medium': 'Standard', 'low': 'Low'}[bucket],
        'source': 'mock',
    }


def draft_sop(context: dict, kind: str) -> dict:
    """Draft a structured document. ALWAYS a draft: a human must approve before use."""
    if not settings.ai_mock():
        raise ModelNotConfigured('Wire Muse Spark in services/ai/muse_spark.py')
    title = {'public_works_sop': 'Public works SOP (draft)',
             'traffic_management_plan': 'Traffic management plan (draft)'}[kind]
    steps = {
        'public_works_sop': ['Confirm permits and utility responses are in place', 'Secure and sign the work area',
                             'Carry out the repair per the recommended action', 'Inspect and close the ticket'],
        'traffic_management_plan': ['Define the affected lanes and sidewalks', 'Place signage and barriers',
                                    'Set a pedestrian detour if the sidewalk is blocked', 'Remove signage after works'],
    }[kind]
    return {
        'title': title, 'kind': kind, 'ticket_ref': context.get('public_ref'),
        'summary': f"{context.get('category')} / severity {context.get('severity')} at "
                   f"({context.get('lat'):.5f}, {context.get('lng'):.5f})",
        'permits': context.get('permits', []),
        'steps': [{'n': i + 1, 'text': s} for i, s in enumerate(steps)],
        'disclaimer': 'AI-generated draft from a mock model. Must be reviewed and approved by a qualified person.',
        'source': 'mock',
    }
