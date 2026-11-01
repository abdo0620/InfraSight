"""All prompts live here. The browser never sends a prompt: it calls the ticket endpoints, which call these."""
import base64, json, logging, re
import httpx, openai
from fastapi import HTTPException
from pydantic import BaseModel, ValidationError
from ..config import settings
from ..regulations import DIRECTORY, REG, STAGES
from ..schemas import Forecast, RepairCheck, Report, SizeEstimate, Triage

# Muse Spark model when MODEL_QUICK / MODEL_DEFAULT are not set in .env; Muse Image for the repair preview
DEFAULT_MODEL = "muse-spark-1.1"
IMAGE_MODEL = "muse-image-1.0"
_clients: dict = {}


def _model(tier: str) -> str:
    return (settings.model_quick if tier == "quick" else settings.model_default) or DEFAULT_MODEL


def _ask_meta(prompt: str, imgs: list[bytes], model: str) -> str:
    """Meta Model API (Muse Spark), OpenAI-compatible Chat Completions."""
    if not settings.meta_api_key:
        raise HTTPException(503, "AI is not configured: set META_API_KEY in backend/.env")
    c = _clients.setdefault("meta", openai.OpenAI(base_url=settings.meta_base_url, api_key=settings.meta_api_key))
    parts = [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(i).decode()}} for i in imgs]
    parts.append({"type": "text", "text": prompt})
    try:
        r = c.chat.completions.create(model=model, messages=[{"role": "user", "content": parts}])
    except openai.RateLimitError:
        raise HTTPException(429, "The AI is busy. Wait a moment and try again.")
    except openai.APIError as e:
        logging.exception("Meta Model API call failed")
        raise HTTPException(502, "The AI could not answer. Try again.") from e
    return r.choices[0].message.content or ""


CONS_JSON = ('"consequences":{"danger_type":"","blocked_access":false,"potential_events":[{"event":"","likelihood":'
             '"low|medium|high","impact":""}],"vulnerable_people":"","immediate_measures":[""]},'
             '"danger_zone":{"shape":"point|street|area","radius_m":0,"level":1-5,"description":""}')
ZONE_RULES = ('Danger zone shape: "street" when the problem blocks or disrupts traffic or passage along a street (hole or '
              "obstacle on the roadway, closed lane, blocked pavement, fallen tree across the road, sunken cover on a busy "
              "road); radius_m is then the length of street affected, and set blocked_access true if vehicles or "
              'pedestrians cannot get through. "area" when the danger spreads in every direction (flooding, gas or water '
              'leak, fire, risk of collapse or falling objects); radius_m is the radius. "point" for a localized problem '
              "that does not disrupt traffic (broken streetlight, small pothole at the edge, waste, graffiti).")
TRIAGE_JSON = ('{"title":"short title","type":"Roads|Lighting|Green spaces|Waste|Water|Other","severity":1-5,"urgency":1-5,'
               '"owner":"commune|department|state|epci|private|network","summary":"one sentence","duplicate_of":"ref or null",'
               '"damage_box":[0,0,0,0],' + CONS_JSON + "}")
BOX_RULE = ("damage_box: where the damage is on the photo, as [x1, y1, x2, y2] fractions of the photo width and height "
            "(0 = left/top, 1 = right/bottom), tight around the damaged part only; null if there is no photo or the "
            "damage is not visible.")
REPORT_JSON = ('{"type":"","severity":1-5,"severity_reason":"","urgency":"immediate|under 48 hours|under 2 weeks|planned",'
               '"response_time":"","authority":{"primary":"","secondary":[""],"contact_reason":""},"ownership_assessment":"",'
               '"regulatory":{"procurement":"","authorizations":[""],"council_vote":true,"legal_notes":[""]},'
               '"cost":{"min":0,"max":0,"basis":""},"risks":[""],"actions":[{"step":"","owner":"","deadline":""}],'
               '"citizen_message":"",' + CONS_JSON + "}")


def _ask(prompt: str, image: bytes | list[bytes] | None, tier: str) -> str:
    """image: one photo, several (before / after) or none."""
    imgs = [i for i in (image if isinstance(image, list) else [image]) if i]
    return _ask_meta(prompt, imgs, _model(tier))


def configured() -> bool:
    return bool(settings.meta_api_key)


def _ask_model(prompt: str, image, tier: str, model: type[BaseModel]) -> BaseModel:
    """Ask for JSON and validate it; one retry if the answer is not valid."""
    for attempt in (1, 2):
        txt = _ask(prompt + "\nReturn only valid JSON.", image, tier)
        try:
            return model.model_validate(json.loads(re.search(r"\{.*\}", txt, re.S).group(0)))
        except (AttributeError, json.JSONDecodeError, ValidationError) as e:
            logging.warning("AI answer was not valid %s (attempt %d): %s", model.__name__, attempt, e)
    raise HTTPException(502, "The AI answer could not be read. Try again.")


def triage(address: str, description: str, open_tickets: list[str], image: bytes | None) -> Triage:
    """open_tickets: "ref title, address (distance)", nearest first."""
    prompt = ("You triage citizen reports for a French commune. Look closely at the photo. Judge what could happen if "
              "nothing is done (blocked road, risk of falling, collision, flooding, fire) and the size of the danger zone "
              f"around the spot. {ZONE_RULES} {BOX_RULE}\nReturn only JSON: {TRIAGE_JSON}\nAddress: {address}\nDescription: {description}\n"
              f"Open tickets (nearest first; set duplicate_of only if one is clearly the same problem at the same place): "
              f"{json.dumps(open_tickets, ensure_ascii=False)}")
    return _ask_model(prompt, image, "quick", Triage)


def full_report(ticket_ctx: dict, image: bytes | None, zone_image: bytes | None = None) -> Report:
    """zone_image: the same photo with the damage marked in red (services/visuals.py), sent second."""
    marked = "The second photo is the same, with the damaged area marked in red. " if image and zone_image else ""
    prompt = ("You are the triage and compliance analyst of a French commune. Use the regulatory notes and the full "
              f"ticket context. {marked}Be specific and cautious; assess the consequences if nothing is done (blocked road, "
              "falling, collision, flooding) and the danger zone around the spot, using the photo if provided; mark "
              f"anything needing legal checks with [verify]. {ZONE_RULES}\nREGULATORY NOTES:\n{REG}\n"
              f"DIRECTORY:\n{json.dumps([d['n'] for d in DIRECTORY], ensure_ascii=False)}\n"
              f"TICKET CONTEXT:\n{json.dumps(ticket_ctx, default=str, ensure_ascii=False)}\nReturn only JSON: {REPORT_JSON}")
    return _ask_model(prompt, [image, zone_image] if image and zone_image else image, "default", Report)


def stage_assist(stage: int, ticket_ctx: dict, image: bytes | None) -> str:
    prompt = ("You are the municipal assistant of a French commune. Use the regulatory notes and the whole ticket "
              "context, including earlier stages. Plain text, no markdown, under 230 words. Mark anything needing legal "
              f"checks with [verify].\nREGULATORY NOTES:\n{REG}\n"
              f"CONTEXT:\n{json.dumps(ticket_ctx, default=str, ensure_ascii=False)}\nTASK: {STAGES[stage]['p']}")
    return _ask(prompt, image, "default")


SIZE_JSON = ('{"width_m":0,"length_m":0,"depth_cm":null,"area_m2":0,"basis":"","confidence":"low|medium|high",'
             '"box":[0,0,0,0]}')


def estimate_size(image: bytes, kind: str, outline: list[dict] | None) -> SizeEstimate:
    """Real size of the damage. outline: SAM boxes as fractions of the photo (x1, y1, x2, y2), if available."""
    where = (f"The damage was outlined by a segmentation model; boxes as fractions of the photo width/height: "
             f"{json.dumps([o['box'] for o in outline])}. Set box to null. " if outline
             else BOX_RULE.replace("damage_box", "box") + " ")
    prompt = (f"Estimate the real size of the {kind} damage in this photo for a repair quote. {where}Use visible references "
              "of known size (kerb about 15 cm high, paving slab, road marking about 15 cm wide, car wheel about 60 cm, "
              "manhole cover about 60 cm, shoe about 28 cm). Say which references you used in basis. If there is no "
              f"reliable reference, give your best estimate with confidence low. Return only JSON: {SIZE_JSON}")
    return _ask_model(prompt, image, "default", SizeEstimate)


def check_repair(before: bytes | None, after: bytes, ticket: dict, marked: bool = False) -> RepairCheck:
    """Compare the citizen photo (first, with the damage marked in red when marked) with the after-repair photo."""
    first = ("The first photo was taken when the problem was reported" + (", with the damaged area marked in red"
             if marked else "") + ", the second after the repair. " if before else
             "There is no photo from the report; judge the repair from this after-repair photo and the description. ")
    prompt = (f"You check public works at acceptance (OPR) for a French commune. {first}Problem: "
              f"{json.dumps(ticket, ensure_ascii=False)}. Is the problem fixed? Look for remaining holes, cracks, "
              "missing signage, debris, poor finishing. Return only JSON: "
              '{"verdict":"repaired|partial|not_repaired|unclear","explanation":"","remaining_issues":[""]}')
    return _ask_model(prompt, [before, after] if before else after, "default", RepairCheck)


def traffic_order(ticket: dict, street: str, length_m: float, detour: list[str]) -> str:
    """Draft of the mayor's traffic order (arrêté) closing the street section, with the computed detour."""
    prompt = ("Draft, in French, the municipal traffic order (arrêté municipal portant réglementation temporaire de la "
              "circulation) for this road closure, ready for the mayor to check and sign. Structure: title, visas (CGCT "
              "L2213-1 and L2213-2, Code de la route, instruction interministérielle sur la signalisation routière), "
              "considérant, articles (section closed, dates [to fill], detour route, signage at the contractor's or "
              "commune's charge, exemptions for emergency vehicles and residents, posting and publication, execution). "
              f"Plain text, no markdown. Mark anything to verify with [verify].\nTicket: {json.dumps(ticket, ensure_ascii=False)}\n"
              f"Section closed: {street}, about {round(length_m)} m.\nDetour (computed from OpenStreetMap, in order): "
              f"{', '.join(detour) or 'not computed'}")
    return _ask(prompt, None, "default")


FORECAST_JSON = ('{"summary":"","hotspots":[{"street":"","risk":"low|medium|high","expected_problem":"","reason":"",'
                 '"preventive_action":"","budget_eur":0}]}')


def forecast(hotspots: list[dict], month: str) -> Forecast:
    prompt = ("You advise the technical services of a French commune on preventive maintenance. Below are the streets "
              "with repeated reports over the last 12 months (count, types, severity, cost, dates). Predict where problems "
              f"are most likely in the coming months (current month: {month}; think of winter frost and potholes, autumn "
              "leaves and blocked drains, storms and trees), and propose preventive actions with a rough budget in euros. "
              "Be cautious: few data points mean low certainty, say so in reason. Return only JSON: "
              f"{FORECAST_JSON}\nHOTSPOTS:\n{json.dumps(hotspots, ensure_ascii=False, default=str)}")
    return _ask_model(prompt, None, "default", Forecast)


def citizen_update(lang: str, ticket: dict, event: str, next_step: str | None) -> str:
    prompt = (f"Write a short, friendly update (under 60 words) in {lang} for a citizen who reported a problem to the "
              "town hall. Plain words, no internal jargon (no CCTP, OPR, DT-DICT), no dates or promises that are not "
              "given below. Do not invent facts.\n"
              f"Report: {json.dumps(ticket, ensure_ascii=False)}\nWhat just happened: {event}\n"
              f"Next step: {next_step or 'none, the case is closed'}")
    return _ask(prompt, None, "quick").strip()


def weekly_brief(facts: dict) -> str:
    prompt = ("Write the weekly brief for the elected officials of a French commune about public space maintenance. "
              "Plain text, no markdown, under 250 words, in English. Sections: Headlines, Safety (dangers and blocked "
              "streets), Decisions waiting for you, Money, Trends. Only use the facts below; say when data is missing.\n"
              f"FACTS:\n{json.dumps(facts, ensure_ascii=False, default=str)}")
    return _ask(prompt, None, "default").strip()


def repair_preview(photo: bytes, marked: bytes | None, kind: str, description: str) -> bytes:
    """Muse Image: the citizen photo with only the damage repaired, to show what the street will look like.
    marked: the same photo with the damage in red, so the model knows what to repair (the API has no mask)."""
    if not settings.meta_api_key:
        raise HTTPException(503, "AI is not configured: set META_API_KEY in backend/.env")
    c = _clients.setdefault("meta", openai.OpenAI(base_url=settings.meta_base_url, api_key=settings.meta_api_key))
    where = ("The second image is the same photo with the damaged area marked in red: repair only that area. " if marked
             else "Repair only the damaged part. ")
    prompt = (f"Show this street photo after a municipal crew repaired the {kind.lower()} problem ({description[:300]}). "
              f"{where}Keep everything else identical: framing, camera angle, light, weather, surroundings, objects. "
              "The repair must look realistic and ordinary (e.g. a pothole filled with fresh asphalt flush with the road, "
              "a working street lamp, rubbish removed, the branch cleared). No red marks, no text, no people added.")
    files = [("photo.jpg", photo, "image/jpeg")] + ([("marked.jpg", marked, "image/jpeg")] if marked else [])
    try:
        r = c.images.edit(model=settings.model_image or IMAGE_MODEL, prompt=prompt,
                          image=files if marked else files[0], n=1)
    except openai.RateLimitError:
        raise HTTPException(429, "The image AI is busy. Wait a moment and try again.")
    except openai.APIError as e:
        logging.exception("Muse Image call failed")
        raise HTTPException(502, "The image AI could not answer. Try again.") from e
    d = r.data[0] if r.data else None
    if d is not None and d.b64_json:
        return base64.b64decode(d.b64_json)
    if d is not None and d.url:
        return httpx.get(d.url, timeout=60).content
    raise HTTPException(502, "The image AI returned no image. Try again.")
