"""Tier 1 AI assessment. NEVER raises: any failure becomes uncategorized/unknown + human review."""
from dataclasses import dataclass, field

from config import feature_flags as flags
from services.ai import muse_spark

SEVERITIES = {'low', 'medium', 'high'}


@dataclass
class Assessment:
    category: str = 'uncategorized'
    severity: str = 'unknown'
    confidence: float | None = None
    uncertainties: list = field(default_factory=list)
    needs_human_review: bool = True
    fallback_reason: str | None = None
    source: str | None = None

    def as_payload(self) -> dict:
        return {'category': self.category, 'severity': self.severity, 'confidence': self.confidence,
                'uncertainties': self.uncertainties, 'needs_human_review': self.needs_human_review,
                'fallback': self.fallback_reason, 'source': self.source}


def assess(image_bytes: bytes) -> Assessment:
    if not flags.is_enabled('ai_assessment_enabled'):
        return Assessment(fallback_reason='flag_disabled')
    try:
        raw = muse_spark.assess_damage(image_bytes)
        severity = raw['severity'] if raw.get('severity') in SEVERITIES else 'unknown'
        category = str(raw['category'])
        return Assessment(category=category, severity=severity, confidence=raw.get('confidence'),
                          uncertainties=list(raw.get('uncertainties', [])),
                          needs_human_review=severity == 'unknown' or (raw.get('confidence') or 0) < 0.5,
                          source=raw.get('source'))
    except Exception as exc:  # noqa: BLE001  (tier 1 must survive any model failure)
        return Assessment(fallback_reason=f'model_error:{type(exc).__name__}')
