"""Images derived from the citizen photo, shown everywhere the ticket is (overview, AI report, danger tab, map popup,
acceptance stage, downloaded report):
- the damage zone: the photo with the damaged area in red (SAM outline, or the box the AI gives at triage / sizing);
- the repair preview: the photo as it should look once repaired (Muse Image), an illustration, not a promise.
Stored in uploads/ next to the photo; their paths go in ticket.data["visual"]."""
import io, logging, secrets
from datetime import date
from pathlib import Path
from fastapi import HTTPException
from PIL import Image, ImageDraw, ImageFilter
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
    else:                                            # no outline: the AI box as it is, a rounded rectangle (a padded
        x1, y1, x2, y2 = box                         # ellipse covered sky and road around a large object)
        e = [max(0, x1 * w), max(0, y1 * h), min(w, x2 * w), min(h, y2 * h)]
        d.rounded_rectangle(e, radius=min(e[2] - e[0], e[3] - e[1]) * 0.12, fill=RED + (60,), outline=RED + (255,),
                            width=width)
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
    t.data = {**(t.data or {}), "visual": {**v, "zone": path, "zone_from": "sam" if objects else "ai",
                                           "zone_box": None if objects else box}}
    return path


def draw_preview(t: Ticket) -> bytes:
    """Ask Muse Image for the repaired photo (slow: about 20 s). Raises HTTPException when it fails."""
    photo = read(t.image_path)
    if not photo:
        raise HTTPException(409, "This ticket has no photo")
    d = t.data or {}
    v = d.get("visual") or {}
    drawn = ai.repair_preview(photo, read(v.get("zone")), t.type, t.desc)
    objects = (d.get("damage") or {}).get("objects")
    box = v.get("zone_box") or (d.get("hint") or {}).get("box")
    return images.normalize(repaired_only(photo, drawn, [o["polygon"] for o in objects] if objects else None, box))


def repaired_only(photo: bytes, drawn: bytes, polygons: list | None, box: list[float] | None) -> bytes:
    """Muse Image redraws the whole photo, and sometimes changes cars, signs or the light far from the damage. Keep
    the real photo and take from the drawing only the damaged area (SAM outlines and/or the AI box, widened, with a
    soft edge). Without an outline or a box, the drawing is used as it is."""
    if not polygons and not box:
        return drawn
    im = Image.open(io.BytesIO(photo)).convert("RGB")
    w, h = im.size
    new = Image.open(io.BytesIO(drawn)).convert("RGB").resize((w, h), Image.LANCZOS)
    mask = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mask)
    # SAM outlines the hole itself; a real patch is cut wider, over the cracked rim: an ellipse 30% wider than each
    # outline is taken from the drawing as well. Several outlines (broken slabs) are one repair: their whole span is
    # taken, plus the AI box when there is one
    boxes = [[min(x for x, _ in p), min(y for _, y in p), max(x for x, _ in p), max(y for _, y in p)]
             for p in polygons or [] if len(p) >= 3]
    if len(boxes) > 1:
        boxes.append([min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes),
                      max(b[3] for b in boxes)])
    if box:
        boxes.append(box)
    for poly in polygons or []:
        if len(poly) >= 3:
            d.polygon([(x * w, y * h) for x, y in poly], fill=255)
    for x1, y1, x2, y2 in boxes:
        bw, bh = (x2 - x1) * 0.3, (y2 - y1) * 0.3
        d.ellipse([(x1 - bw) * w, (y1 - bh) * h, (x2 + bw) * w, (y2 + bh) * h], fill=255)
    grow = max(3, round(min(w, h) * 0.025))         # covers the edge of the hole and the fresh asphalt joint
    mask = mask.filter(ImageFilter.GaussianBlur(grow)).point(lambda p: 255 if p > 8 else 0)  # widen
    mask = mask.filter(ImageFilter.GaussianBlur(grow / 2))                                  # soft edge
    out = io.BytesIO()
    Image.composite(new, im, mask).save(out, "JPEG", quality=90)
    return out.getvalue()


def store_preview(t: Ticket, img: bytes) -> str:
    v = (t.data or {}).get("visual") or {}
    _drop(v.get("preview"))
    path = _save(t.ref, img, "preview")
    t.data = {**(t.data or {}), "visual": {**v, "preview": path, "preview_error": None, "pending": False}}
    return path


def make_preview(t: Ticket) -> str:
    """Draw the repaired photo and store it on the ticket (staff buttons). Raises HTTPException when it fails."""
    return store_preview(t, draw_preview(t))


def preview_later(ref: str) -> None:
    """Background task after a citizen report (FastAPI BackgroundTasks), nobody waits for it:
    SAM 3.1 outlines the damage (exact red zone instead of the triage box), then Muse Image draws the repair.
    The slow AI calls run with no ticket loaded; each result is saved on a freshly loaded ticket, so changes made
    meanwhile by a request (a merged duplicate, a staff action) are kept."""
    with SessionLocal() as s:
        t = s.get(Ticket, ref)
        if not t:
            return
        photo, kind, hint = read(t.image_path), t.type, (t.data or {}).get("hint") or {}
    sam, objects = "none", None                       # what the live pipeline on the report page shows
    try:
        objects = vision.outline(photo, kind, hint.get("label"), hint.get("box")) if photo else None
        sam = "done" if objects else "none"
    except HTTPException as e:                        # keep the triage box
        logging.warning("SAM outline for %s not made: %s", ref, e.detail)
        sam = "error"
    with SessionLocal() as s:
        t = s.get(Ticket, ref)
        if objects:
            t.data = {**(t.data or {}), "damage": {"objects": objects, "size": None, "sam": True}}
            path = set_zone(t, photo, objects)
            t.audit.append(Audit(d=date.today().isoformat(), user_id=None, has_img=False, image_path=path,
                                 w="AI assistant", e=f"Damage outlined by SAM 3.1 ({len(objects)} area"
                                                      f"{'s' if len(objects) > 1 else ''})" + AI_TAG))
        t.data = {**(t.data or {}), "visual": {**((t.data or {}).get("visual") or {}), "sam": sam}}
        s.commit()                                    # SAM result visible now, while Muse Image is still drawing
        s.refresh(t)
        s.expunge(t)                                  # detached copy, only to read the photo and zone below
    img, err = None, None
    try:
        img = draw_preview(t)
    except HTTPException as e:
        logging.warning("Repair preview for %s not made: %s", ref, e.detail)
        err = e.detail
    with SessionLocal() as s:
        t = s.get(Ticket, ref)
        if img:
            path = store_preview(t, img)
            t.audit.append(Audit(d=date.today().isoformat(), user_id=None, has_img=False, image_path=path,
                                 w="AI assistant", e="Repair preview drawn (illustration)" + AI_TAG))
        else:
            vis = (t.data or {}).get("visual") or {}
            t.data = {**(t.data or {}), "visual": {**vis, "preview_error": err, "pending": False}}
        s.commit()
