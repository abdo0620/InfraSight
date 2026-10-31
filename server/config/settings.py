"""Runtime settings, read from the environment at call time (so tests can change them)."""
import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RULES_DIR = BASE_DIR / 'compliance-rules'
SEEDS_DIR = BASE_DIR / 'db' / 'seeds'
CLIENT_DIR = BASE_DIR.parent / 'client'

_EPHEMERAL_KEY = secrets.token_hex(32)


def database_url() -> str:
    return os.environ.get('DATABASE_URL', f"sqlite:///{BASE_DIR / 'infrasight.db'}")


def secret_key() -> str:
    # Without SECRET_KEY, tokens only survive until restart (and not across workers).
    return os.environ.get('SECRET_KEY', _EPHEMERAL_KEY)


def upload_dir() -> Path:
    p = Path(os.environ.get('UPLOAD_DIR', BASE_DIR / 'storage' / 'uploads'))
    p.mkdir(parents=True, exist_ok=True)
    return p


def max_upload_bytes() -> int:
    return int(os.environ.get('MAX_UPLOAD_BYTES', 10 * 1024 * 1024))


def ai_mock() -> bool:
    return os.environ.get('AI_MOCK', '1').lower() in ('1', 'true', 'yes', 'on')


def enrichment_retries() -> int:
    return max(1, int(os.environ.get('ENRICHMENT_RETRIES', 3)))


def enrichment_backoff_s() -> float:
    return float(os.environ.get('ENRICHMENT_BACKOFF_S', 0.5))


def cors_origins() -> list[str]:
    raw = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:8000')
    return [o.strip() for o in raw.split(',') if o.strip()]
