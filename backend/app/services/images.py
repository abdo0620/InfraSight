import io
from fastapi import HTTPException
from PIL import Image
from ..config import settings


def normalize(raw: bytes) -> bytes:
    """Validate and shrink the citizen photo to a 1280 px JPEG (stored once, reused everywhere)."""
    if len(raw) > settings.max_image_mb * 1024 * 1024:
        raise HTTPException(413, "Image too large")
    try:
        im = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        raise HTTPException(400, "Not a valid image")
    im.thumbnail((1280, 1280))
    out = io.BytesIO()
    im.save(out, "JPEG", quality=85)
    return out.getvalue()
