"""SAM 3.1 outlines the damage on a photo. Two ways to reach it:
- the Meta Model API (model sam-3.1, POST /v1/responses), used when META_API_KEY is set and SAM_URL is empty: no GPU
  needed, about $0.0025 per image (https://dev.meta.ai/docs/media-segmentation);
- your own SAM server (sam_server/ in this project), when SAM_URL is set."""
import asyncio, base64, io, logging, re
import httpx, openai
from fastapi import HTTPException
from meta_sam_parser import decode_mask_to_raster, decode_mask_to_svg_path, image_segmentation_format, parse_responses_stream
from PIL import Image
from ..config import settings

# What SAM looks for, per ticket type (SAM 3 takes a short noun phrase: one concept, no "and", no commas)
PROMPTS = {"Roads": "pothole", "Lighting": "street lamp", "Green spaces": "fallen tree branch", "Waste": "pile of rubbish",
           "Water": "water puddle"}
SAM_MODEL = "sam-3.1"
MAX_OBJECTS = 5


def outline(image: bytes, kind: str) -> list[dict] | None:
    """[{"score", "box": [x1, y1, x2, y2], "polygon": [[x, y], ...], "area"}], all as fractions of the photo size,
    best first. None when SAM is not available (no SAM_URL and no META_API_KEY)."""
    text = PROMPTS.get(kind, "damage")
    if settings.sam_url:
        return _own_server(image, text)
    if settings.meta_api_key:
        return _model_api(image, text)
    return None


def _own_server(image: bytes, text: str) -> list[dict]:
    try:
        r = httpx.post(settings.sam_url.rstrip("/") + "/segment", timeout=180,
                       files={"image": ("photo.jpg", image, "image/jpeg")}, data={"text": text})
        r.raise_for_status()
        return r.json()["objects"]
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logging.warning("SAM server failed: %s", e)
        raise HTTPException(502, "The SAM server could not answer. Check SAM_URL in backend/.env.") from e


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
