"""Images derived from the citizen photo, shown everywhere the ticket is (overview, AI report, danger tab, map popup,
acceptance stage, downloaded report):
- the damage zone: the photo with the damaged area in red (SAM outline, or the box the AI gives at triage / sizing);
- the repair preview: the photo as it should look once repaired (Muse Image), an illustration, not a promise.
Stored in uploads/ next to the photo; their paths go in ticket.data["visual"]."""
import io, logging, secrets
from datetime import date
from pathlib import Path
from fastapi import HTTPException
from PIL import Image, ImageDraw
from ..config import settings
from ..db import Audit, SessionLocal, Ticket
from . import ai, images, vision

RED = (239, 68, 68)
AI_TAG = " [AI-generated, human review required]"   # same tag as routers/tickets.py


def _save(ref: str, img: bytes, kind: str) -> str:
    """New file name each time, so a browser never shows an old cached version."""
    path = Path(settings.upload_dir) / f"{ref}-{kind}-{secrets.token_hex(3)}.jpg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(img)
    return str(path)


def _drop(path: str | None) -> None:
    if path:
        Path(path).unlink(missing_ok=True)


def read(path: str | None) -> bytes | None:
    return Path(path).read_bytes() if path and Path(path).exists() else None


def overlay(photo: bytes, polygons: list[list[list[float]]] | None = None, box: list[float] | None = None) -> bytes | None:
    """The photo with the damage in translucent red and a red outline. polygons (SAM) or box, as photo fractions."""
    if not polygons and not box:
        return None
    im = Image.open(io.BytesIO(photo)).convert("RGB")
    w, h = im.size
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    width = max(3, round(min(w, h) / 160))
    if polygons:
        for poly in polygons:
            pts = [(x * w, y * h) for x, y in poly]
            if len(pts) >= 3:
                d.polygon(pts, fill=RED + (80,))
                d.line(pts + pts[:1], fill=RED + (255,), width=width, joint="curve")
    else:
        x1, y1, x2, y2 = box
        pad = 0.15                                   # the box is tight: draw the zone a little wider, as an ellipse
        bw, bh = (x2 - x1) * pad, (y2 - y1) * pad
        e = [max(0, (x1 - bw) * w), max(0, (y1 - bh) * h), min(w, (x2 + bw) * w), min(h, (y2 + bh) * h)]
        d.ellipse(e, fill=RED + (70,), outline=RED + (255,), width=width)
    out = io.BytesIO()
    Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB").save(out, "JPEG", quality=85)
    return out.getvalue()


def set_zone(t: Ticket, photo: bytes, objects: list[dict] | None = None, box: list[float] | None = None) -> str | None:
    """Draw and store the damage zone on the ticket (replaces the previous one). Returns its path, or None."""
    img = overlay(photo, [o["polygon"] for o in objects] if objects else None, box)
    if not img:
        return None
    v = (t.data or {}).get("visual") or {}
    _drop(v.get("zone"))
    path = _save(t.ref, img, "zone")
    t.data = {**(t.data or {}), "visual": {**v, "zone": path, "zone_from": "sam" if objects else "ai"}}
    return path


def make_preview(t: Ticket) -> str:
    """Ask Muse Image for the repaired photo and store it on the ticket. Raises HTTPException when it fails."""
    photo = read(t.image_path)
    if not photo:
        raise HTTPException(409, "This ticket has no photo")
    v = (t.data or {}).get("visual") or {}
    img = images.normalize(ai.repair_preview(photo, read(v.get("zone")), t.type, t.desc))
    _drop(v.get("preview"))
    path = _save(t.ref, img, "preview")
    t.data = {**(t.data or {}), "visual": {**v, "preview": path, "preview_error": None, "pending": False}}
    return path


def preview_later(ref: str) -> None:
    """Background task after a citizen report (FastAPI BackgroundTasks), nobody waits for it:
    SAM 3.1 outlines the damage (exact red zone instead of the triage box), then Muse Image draws the repair."""
    with SessionLocal() as s:
        t = s.get(Ticket, ref)
        if not t:
            return
        photo = read(t.image_path)
        try:
            objects = vision.outline(photo, t.type) if photo else None
            if objects:
                t.data = {**(t.data or {}), "damage": {"objects": objects, "size": None, "sam": True}}
                path = set_zone(t, photo, objects)
                t.audit.append(Audit(d=date.today().isoformat(), user_id=None, has_img=False, image_path=path,
                                     w="AI assistant", e=f"Damage outlined by SAM 3.1 ({len(objects)} area"
                                                          f"{'s' if len(objects) > 1 else ''})" + AI_TAG))
        except HTTPException as e:                   # keep the triage box
            logging.warning("SAM outline for %s not made: %s", ref, e.detail)
        try:
            path = make_preview(t)
            t.audit.append(Audit(d=date.today().isoformat(), user_id=None, has_img=False, image_path=path,
                                 w="AI assistant", e="Repair preview drawn (illustration)" + AI_TAG))
        except HTTPException as e:
            logging.warning("Repair preview for %s not made: %s", ref, e.detail)
            v = (t.data or {}).get("visual") or {}
            t.data = {**(t.data or {}), "visual": {**v, "preview_error": e.detail, "pending": False}}
        s.commit()
