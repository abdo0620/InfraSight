"""SAM 3.1 client. Mock mode draws an irregular blob around the tapped point."""
import io
import math

from PIL import Image, ImageDraw

from config import settings
from services.ai.errors import ModelNotConfigured


def segment(image_bytes: bytes, x: float, y: float) -> bytes:
    """Return a PNG mask: opaque where the damage is, transparent elsewhere."""
    if not settings.ai_mock():
        raise ModelNotConfigured('Wire SAM 3.1 in services/ai/sam.py')
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    cx, cy, rx, ry, n = x * w, y * h, w * 0.13, h * 0.085, 36
    pts = []
    for i in range(n):
        a = i / n * math.tau
        k = 1 + 0.18 * math.sin(a * 3 + 1.3) + 0.1 * math.sin(a * 5 + 0.4)
        pts.append((cx + math.cos(a) * rx * k, cy + math.sin(a) * ry * k))
    mask = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(mask).polygon(pts, fill=(255, 255, 255, 255))
    out = io.BytesIO()
    mask.save(out, 'PNG')
    return out.getvalue()
