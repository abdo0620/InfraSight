"""Tier 1 intake: validation, EXIF stripping, storage, duplicate detection."""
import hashlib
import io
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from db.models.core import Ticket, Upload

DUPLICATE_WINDOW = timedelta(hours=24)
MIN_SIDE_PX = 320


class IntakeError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


@dataclass
class ValidatedReport:
    image_bytes: bytes
    ext: str
    lat: float
    lng: float
    description: str
    sha256: str
    quality_flags: list = field(default_factory=list)


def _clean_image(data: bytes) -> tuple[bytes, str, list]:
    """Decode, flag quality problems and re-encode WITHOUT metadata (strips GPS/EXIF)."""
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except (UnidentifiedImageError, OSError):
        raise IntakeError('invalid_image', 'This file is not a readable photo. Please upload a JPEG, PNG or WebP image.')
    fmt = (img.format or '').upper()
    if fmt not in ('JPEG', 'PNG', 'WEBP'):
        raise IntakeError('invalid_image', 'Unsupported image type. Please upload a JPEG, PNG or WebP image.')
    flags = ['low_resolution'] if min(img.size) < MIN_SIDE_PX else []
    clean = Image.new(img.mode, img.size)
    clean.paste(img)
    buf = io.BytesIO()
    if fmt == 'JPEG':
        clean.convert('RGB').save(buf, 'JPEG', quality=90)
    else:
        clean.save(buf, fmt)
    return buf.getvalue(), {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp'}[fmt], flags


def validate(data: bytes, lat, lng, description: str | None) -> ValidatedReport:
    if not data:
        raise IntakeError('missing_image', 'Please attach a photo of the damage.')
    if len(data) > settings.max_upload_bytes():
        raise IntakeError('image_too_large', 'The photo is too large. Please upload one under 10 MB.')
    if lat is None or lng is None:
        raise IntakeError('missing_location', 'Please share the location of the damage.')
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise IntakeError('invalid_location', 'The location is not valid. Please pick it again on the map.')
    cleaned, ext, flags = _clean_image(data)
    return ValidatedReport(cleaned, ext, float(lat), float(lng), (description or '').strip()[:2000],
                           hashlib.sha256(cleaned).hexdigest(), flags)


def find_duplicate(db: Session, report: ValidatedReport) -> Ticket | None:
    """Same photo within 24h of an existing report -> that ticket."""
    since = datetime.now(timezone.utc) - DUPLICATE_WINDOW
    uploads = db.scalars(select(Upload).where(Upload.kind == 'citizen_report', Upload.created_at >= since.replace(tzinfo=None))).all()
    for u in uploads:
        if (u.meta or {}).get('sha256') == report.sha256 and u.ticket_id:
            return db.get(Ticket, u.ticket_id)
    return None


def store_upload(db: Session, report: ValidatedReport) -> Upload:
    key = f'{uuid.uuid4()}.{report.ext}'
    (settings.upload_dir() / key).write_bytes(report.image_bytes)
    up = Upload(kind='citizen_report', storage_key=key,
                meta={'sha256': report.sha256, 'bytes': len(report.image_bytes), 'quality_flags': report.quality_flags})
    db.add(up)
    db.commit()
    return up
