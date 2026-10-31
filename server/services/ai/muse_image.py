"""Muse Image client. Mock mode fills the masked area with the surrounding average color."""
import io

from PIL import Image, ImageFilter, ImageOps, ImageStat

from config import settings
from services.ai.errors import ModelNotConfigured


def repair(image_bytes: bytes, mask_bytes: bytes) -> bytes:
    """Return a JPEG where only the masked area has been 'repaired'."""
    if not settings.ai_mock():
        raise ModelNotConfigured('Wire Muse Image in services/ai/muse_image.py')
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    alpha = Image.open(io.BytesIO(mask_bytes)).convert('RGBA').split()[3].resize(img.size)
    outside = ImageOps.invert(alpha)
    avg = tuple(int(v) for v in ImageStat.Stat(img, mask=outside).mean[:3])
    patch = Image.new('RGB', img.size, avg)
    out = Image.composite(patch, img, alpha.filter(ImageFilter.GaussianBlur(3)))
    buf = io.BytesIO()
    out.save(buf, 'JPEG', quality=90)
    return buf.getvalue()
