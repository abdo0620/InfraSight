"""Client for the SAM 3.1 server (sam_server/ in this project): outlines the damage on a photo."""
import logging
import httpx
from fastapi import HTTPException
from ..config import settings

# What SAM looks for, per ticket type (SAM 3 takes a short noun phrase)
PROMPTS = {"Roads": "pothole", "Lighting": "street lamp", "Green spaces": "fallen tree branch", "Waste": "pile of rubbish",
           "Water": "water puddle"}


def outline(image: bytes, kind: str) -> list[dict] | None:
    """[{"score", "box": [x1, y1, x2, y2], "polygon": [[x, y], ...], "area"}], all as fractions of the photo size.
    None when SAM_URL is not set."""
    if not settings.sam_url:
        return None
    try:
        r = httpx.post(settings.sam_url.rstrip("/") + "/segment", timeout=180,
                       files={"image": ("photo.jpg", image, "image/jpeg")}, data={"text": PROMPTS.get(kind, "damage")})
        r.raise_for_status()
        return r.json()["objects"]
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logging.warning("SAM server failed: %s", e)
        raise HTTPException(502, "The SAM server could not answer. Check SAM_URL in backend/.env.") from e
