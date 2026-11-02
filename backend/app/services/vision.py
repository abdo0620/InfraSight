"""SAM 3.1 outlines the damage on a photo, through the Meta Model API (model sam-3.1, POST /v1/responses):
runs on Meta's servers, about $0.0025 per image (https://dev.meta.ai/docs/media-segmentation)."""
import asyncio, base64, io, logging, re
import openai
from fastapi import HTTPException
from meta_sam_parser import decode_mask_to_raster, decode_mask_to_svg_path, image_segmentation_format, parse_responses_stream
from PIL import Image
from ..config import settings

# What SAM looks for, per ticket type, tried in order (SAM 3 takes a short noun phrase: one concept, no "and", no
# commas). One word per type missed a lot: a crack is not a "pothole", a gushing leak is not a "puddle".
PROMPTS = {"Roads": ["pothole", "cracked asphalt", "broken paving slab"],
           "Lighting": ["street lamp", "broken street light"],
           "Green spaces": ["fallen tree branch", "fallen tree"],
           "Waste": ["pile of rubbish", "garbage bag", "litter"],
           "Water": ["water leak", "water puddle", "flooded road"],
           "Other": ["bus shelter", "bench", "graffiti"]}
# SAM matches what a thing IS, not its state: on a smashed bus shelter "bus shelter" scored 0.68 where "damaged bus
# shelter", "shattered glass" and "broken glass on the ground" found nothing. These words are taken off the label.
STATE_WORDS = re.compile(r"\b(damaged|broken|shattered|smashed|destroyed|vandali[sz]ed|collapsed|bent|burnt|burned|"
                         r"leaking|overflowing|dirty|faulty|defective|missing)\b\s*", re.I)
MAX_BOX_AREA = 0.3     # a looser AI box makes the box prompt outline whatever object is largest inside it
SAM_MODEL = "sam-3.1"
MAX_OBJECTS = 8
MAX_TRIES = 3          # phrase calls per outline at most (about $0.0025 and 3-6 s each), plus one box prompt
MAX_AREA = 0.5         # an object covering half the photo is the whole road or wall, not the damage
MIN_SCORE = 0.25       # SAM returns every match it sees; weaker ones are mostly look-alikes
BOX_LABEL = "area located by the AI"


def outline(image: bytes, kind: str, label: str | None = None, near: list[float] | None = None) -> list[dict] | None:
    """[{"score", "box": [x1, y1, x2, y2], "polygon": [[x, y], ...], "area", "label"}], all as fractions of the
    photo size, best first. None when there is no META_API_KEY.
    label: what the triage AI saw on the photo ("cracked asphalt"), tried first. near: the triage damage box.
    With near, every phrase is tried and the outlines that overlap the box are kept together (a broken bus shelter
    is the shelter AND the glass on the ground); if no phrase finds anything there, SAM gets the box itself as a
    prompt and outlines what is inside it. Without near, the first phrase that finds something wins."""
    if not settings.meta_api_key:
        return None
    plain = STATE_WORDS.sub("", label or "")
    tries = list(dict.fromkeys(" ".join(x.split()).lower() for x in [label or "", plain, *PROMPTS.get(kind, ["damage"])]
                               if x.strip()))
    found, elsewhere = [], []
    for text in tries[:MAX_TRIES]:
        objects = [o | {"label": text} for o in _model_api(image, text) if o["area"] <= MAX_AREA
                   and o["score"] >= MIN_SCORE]
        if not near:
            if objects:
                return objects[:MAX_OBJECTS]
            continue
        found += [o for o in objects if _overlaps(o["box"], near)]
        elsewhere = elsewhere or [o for o in objects if not _overlaps(o["box"], near)]
    if near and not found and (near[2] - near[0]) * (near[3] - near[1]) <= MAX_BOX_AREA:
        found = [o | {"label": BOX_LABEL} for o in _model_api(image, _box_prompt(image, near)) if o["area"] <= MAX_AREA]
    return _distinct(found)[:MAX_OBJECTS] or elsewhere[:MAX_OBJECTS]


def _box_prompt(image: bytes, box: list[float]) -> str:
    """SAM 3.1 object prompt: object 1 is what lies in this box (photo fractions -> pixels, x2/y2 inclusive).
    Grammar from https://dev.meta.ai/docs/sam/segmenting"""
    w, h = Image.open(io.BytesIO(image)).size
    x1, y1, x2, y2 = (round(max(0.0, min(1.0, v)) * s) for v, s in zip(box, (w, h, w, h)))
    return f"<0f>1<|box;x1={x1};y1={y1};x2={min(x2, w - 1)};y2={min(y2, h - 1)};w={w};h={h}|>"


def _distinct(objects: list[dict]) -> list[dict]:
    """Best first, without the same object found twice by two phrases (boxes overlapping by more than half)."""
    def iou(a, b):
        ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
        union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - ix
        return ix / union if union > 0 else 0
    out = []
    for o in sorted(objects, key=lambda o: -o["score"]):
        if all(iou(o["box"], k["box"]) <= 0.5 for k in out):
            out.append(o)
    return out


def _overlaps(a: list[float], b: list[float], pad: float = 0.08) -> bool:
    """Boxes as photo fractions; b grown by pad, since the triage box is only approximate."""
    return a[0] < b[2] + pad and a[2] > b[0] - pad and a[1] < b[3] + pad and a[3] > b[1] - pad


async def _events(image: bytes, text: str):
    """The streamed answer of sam-3.1 (Responses API, OpenAI-compatible). Replaced in tests."""
    client = openai.AsyncOpenAI(base_url=settings.meta_base_url, api_key=settings.meta_api_key)
    try:
        stream = await client.responses.create(
            model=SAM_MODEL, stream=True, metadata={"include_confidence": "true"},
            input=[{"type": "message", "role": "user", "content": [
                {"type": "input_text", "text": text},
                {"type": "input_image", "image_url": "data:image/jpeg;base64," + base64.b64encode(image).decode()}]}])
        async for event in stream:
            yield event
    finally:
        await client.close()


async def _segment(image: bytes, text: str):
    return await parse_responses_stream(_events(image, text), image_segmentation_format()).final_result()


def _model_api(image: bytes, text: str) -> list[dict]:
    """SAM 3.1 over the Meta Model API. Runs in FastAPI's thread pool (sync endpoint), so asyncio.run is safe here."""
    try:
        result = asyncio.run(_segment(image, text))
    except openai.RateLimitError as e:
        raise HTTPException(429, "SAM 3.1 is busy. Wait a moment and try again.") from e
    except Exception as e:                       # API error, or an answer the parser cannot read
        logging.warning("SAM 3.1 (Model API) failed: %s", e)
        raise HTTPException(502, "SAM 3.1 could not outline the damage. Try again.") from e
    return to_objects(result.records, *Image.open(io.BytesIO(image)).size)


def to_objects(records, width: int, height: int) -> list[dict]:
    """Parser records (a box, then its mask, per object; pixels) -> outline objects as photo fractions."""
    boxes, masks = {}, {}
    for r in records:
        if getattr(r, "kind", None) == "box":
            boxes[r.object_id] = r
        elif getattr(r, "kind", None) == "mask":
            masks[r.object_id] = r
    objects = []
    for oid, b in boxes.items():
        m = masks.get(oid)
        poly, area = (_polygon(m, width, height) if m else (None, None))
        box = [b.left / width, b.top / height, b.right / width, b.bottom / height]
        if not poly:                             # no usable mask: the box itself
            poly = [[box[0], box[1]], [box[2], box[1]], [box[2], box[3]], [box[0], box[3]]]
            area = (box[2] - box[0]) * (box[3] - box[1])
        score = b.confidence if b.confidence is not None else (m.confidence if m and m.confidence is not None else 1.0)
        objects.append({"score": round(score, 3), "box": [round(v, 4) for v in box],
                        "polygon": [[round(x, 4), round(y, 4)] for x, y in poly], "area": round(area, 4)})
    objects.sort(key=lambda o: -o["score"])
    return objects[:MAX_OBJECTS]


def _polygon(m, width: int, height: int) -> tuple[list[list[float]] | None, float | None]:
    """Largest outline of a box-local mask, placed in the photo. The mask raster is stretched over its bounds."""
    mask, bd = m.mask, m.bounds
    sx, sy = (bd.right - bd.left) / mask.width, (bd.bottom - bd.top) / mask.height
    rings = []
    for sub in re.split(r"(?=M)", decode_mask_to_svg_path(mask)):
        nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", sub)]
        pts = [((bd.left + nums[i] * sx) / width, (bd.top + nums[i + 1] * sy) / height) for i in range(0, len(nums) - 1, 2)]
        if len(pts) >= 3:
            rings.append(pts)
    if not rings:
        return None, None
    shoelace = lambda p: abs(sum(p[i][0] * p[i - 1][1] - p[i - 1][0] * p[i][1] for i in range(len(p)))) / 2
    covered = sum(decode_mask_to_raster(mask)) / (mask.width * mask.height)
    return [list(p) for p in max(rings, key=shoelace)], covered * (bd.right - bd.left) * (bd.bottom - bd.top) / (width * height)
