"""Jurisdiction provider. Sandbox: bounding boxes from compliance-rules/jurisdiction-rules/*.json.
Replace with a geocoding / boundary service in production."""
import json

from config import settings


class SandboxProvider:
    def locate(self, lat: float, lng: float) -> dict | None:
        for f in sorted((settings.RULES_DIR / 'jurisdiction-rules').glob('*.json')):
            rule = json.loads(f.read_text(encoding='utf-8'))
            min_lng, min_lat, max_lng, max_lat = rule['bbox']
            if min_lng <= lng <= max_lng and min_lat <= lat <= max_lat:
                return {'code': rule['code'], 'confidence': 0.6, 'source': 'sandbox-bbox'}
        return None


def get_provider():
    return SandboxProvider()
