"""Single source of truth for feature flags. Read per call from env: FLAG_<NAME>=1|0.
Tier 1 has no flag: it is the product."""
import os

DEFAULTS = {
    'tier2_admin_enabled': True,
    'tier3_compliance_enabled': False,
    'tier3_utility_alerts_enabled': True,   # only effective when tier 3 is on
    'tier3_sop_generation_enabled': True,   # only effective when tier 3 is on
    'ai_assessment_enabled': True,
}


def is_enabled(name: str) -> bool:
    if name not in DEFAULTS:
        raise KeyError(f'Unknown flag: {name}')
    raw = os.environ.get('FLAG_' + name.upper())
    if raw is None:
        return DEFAULTS[name]
    return raw.strip().lower() in ('1', 'true', 'yes', 'on')


def tier3_utility_alerts() -> bool:
    return is_enabled('tier3_compliance_enabled') and is_enabled('tier3_utility_alerts_enabled')


def tier3_sop() -> bool:
    return is_enabled('tier3_compliance_enabled') and is_enabled('tier3_sop_generation_enabled')


def all_flags() -> dict:
    return {name: is_enabled(name) for name in DEFAULTS}
