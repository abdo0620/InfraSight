"""Sample tickets (and optional demo users) for an empty database. Enabled with SEED_DEMO=true.
Every sample has a photo, like every real report. The photos in demo_photos/ were generated once with Muse Image,
then outlined with SAM 3.1 (zone) and repaired with Muse Image (preview): the same pipeline as a real report.
They are copied to uploads/ when the database is created, so no AI call is made at start."""
import json, logging, shutil
from datetime import datetime, timedelta
from pathlib import Path
from .auth import hash_password
from .config import settings
from .db import Audit, SessionLocal, Ticket, User
from .regulations import STAGES
from .services import geo

# own: reported by the demo citizen. lat, lng, age in days
SAMPLES = [
    dict(id=42, title="Pothole, Rue des Lilas", type="Roads", addr="12 Rue des Lilas", owner="commune", st=2, sev=4, urg=4,
         cost=(2400, 3100), due=2, own=1, geo=(48.3897, -4.4902), age=2,
         desc="Pothole about 40 cm wide and 8 cm deep, 30 m from the school entrance. Two cyclists reported falls this week.",
         cons={"danger_type": "Fall hazard for cyclists near a school", "blocked_access": False,
               "potential_events": [{"event": "Cyclist falls at the school entrance", "likelihood": "high",
                                     "impact": "Injuries to children and cyclists"}],
               "vulnerable_people": "Schoolchildren, cyclists",
               "immediate_measures": ["Cone off the pothole", "Cold-patch repair within 24 h"]},
         zone={"shape": "point", "radius_m": 30, "level": 4, "description": "Approach to the school entrance"}),
    dict(id=44, title="Sunken manhole cover, RD 14", type="Roads", addr="Avenue Foch (RD 14)", owner="department", st=0,
         sev=4, urg=5, cost=(1800, 2200), due=-1, own=0, geo=(48.39245, -4.48755), age=0,
         desc="Cover sunken about 3 cm on a busy departmental road. Cars swerve.",
         cons={"danger_type": "Collision risk, traffic disrupted on RD 14", "blocked_access": False,
               "potential_events": [{"event": "Cars swerve into the oncoming lane", "likelihood": "medium",
                                     "impact": "Collision"}],
               "vulnerable_people": "Drivers, cyclists", "immediate_measures": ["Signage and speed limit", "Raise the cover"]},
         zone={"shape": "street", "radius_m": 200, "level": 4, "description": "RD 14 section around the cover"}),
    dict(id=46, title="Cracked pavement, Rue Victor Hugo", type="Roads", addr="Rue Victor Hugo", owner="commune", st=3,
         sev=3, urg=2, cost=(18500, 22000), due=6, own=0, geo=(48.39070, -4.47852), age=15,
         desc="120 m of pavement cracked by tree roots. Pushchairs and wheelchairs blocked.",
         cons={"danger_type": "Pavement blocked for pushchairs and wheelchairs", "blocked_access": True,
               "potential_events": [{"event": "Users forced onto the roadway", "likelihood": "medium",
                                     "impact": "Collision risk with vehicles"}],
               "vulnerable_people": "Wheelchair users, parents with pushchairs",
               "immediate_measures": ["Mark a safe detour", "Fence off the worst sections"]},
         zone={"shape": "street", "radius_m": 120, "level": 3, "description": "120 m of cracked pavement"}),
    dict(id=47, title="Water main leak, Place de la Liberté", type="Water", addr="Place de la Liberté", owner="epci", st=0,
         sev=5, urg=5, cost=None, due=0, own=0, geo=(48.3896, -4.4858), age=0,
         desc="Water gushing from the ground, the square is flooding and the water reaches the tram stop.",
         cons={"danger_type": "Flooding, slippery ground, possible ground collapse", "blocked_access": True,
               "potential_events": [{"event": "Pedestrian slips or falls into a collapse", "likelihood": "medium",
                                     "impact": "Serious injury"}],
               "vulnerable_people": "Pedestrians, tram passengers", "immediate_measures": ["Close the square", "Call the water service"]},
         zone={"shape": "area", "radius_m": 90, "level": 5, "description": "Flooded square and tram stop"}),
]
# street of each sample, so hotspots work without asking OpenStreetMap
STREETS = {42: "Rue des Lilas", 44: "Avenue du Maréchal Foch", 46: "Rue Victor Hugo", 47: "Place de la Liberté"}
PHOTOS = Path(__file__).parent / "demo_photos"   # IS-00NN-photo.jpg, -zone.jpg, -preview.jpg, -outline.json
DEMO_USERS = [("citizen", "Demo citizen", "citizen"), ("tech", "Demo technician", "tech"),
              ("elected", "Demo elected official", "elected")]


def seed() -> None:
    if not settings.seed_demo:
        return
    with SessionLocal() as s:
        citizen = None
        if settings.demo_password:
            for username, name, role in DEMO_USERS:
                u = s.query(User).filter_by(username=username).first()
                if not u:
                    u = User(username=username, name=name, role=role, password_hash=hash_password(settings.demo_password))
                    s.add(u)
                    logging.warning("Created demo user %r (%s)", username, role)
                if role == "citizen":
                    citizen = u
            s.flush()
        now = datetime.utcnow()
        empty = not s.query(Ticket).count()
        for x in SAMPLES if empty else []:
            ch = {f"{st}:{i}": 1 for st in range(x["st"]) for i in range(len(STAGES[st]["c"]))}
            ref = f"IS-{x['id']:04d}"
            pics = _demo_photos(ref)
            s.add(Ticket(ref=f"IS-{x['id']:04d}", id=x["id"], title=x["title"], type=x["type"], addr=x["addr"],
                         owner=x["owner"], reporter_id=citizen.id if citizen and x["own"] else None, desc=x["desc"],
                         lat=x["geo"][0], lng=x["geo"][1], st=x["st"], sev=x["sev"], urg=x["urg"], due=x["due"],
                         cost_min=x["cost"] and x["cost"][0], cost_max=x["cost"] and x["cost"][1], created=now - timedelta(days=x["age"]),
                         image_path=pics.get("photo"),
                         data={"cons": x.get("cons"), "zone": x.get("zone"), "rep": None, "ai": {}, "ch": ch,
                               "street_name": STREETS.get(x["id"]),
                               "visual": {"zone": pics.get("zone"), "zone_from": "sam", "preview": pics.get("preview")},
                               "damage": {"objects": pics.get("outline", []), "size": None, "sam": True}},
                         audit=[Audit(d="Opened", w="Citizen portal", e="Report received and registered"),
                                Audit(d="Opened", w="Citizen portal", e="Photo attached by the citizen", has_img=True)]))
        s.commit()


def _demo_photos(ref: str) -> dict:
    """Copy the demo images of one sample to uploads/ and return their paths (and the SAM outline)."""
    out, up = {}, Path(settings.upload_dir)
    up.mkdir(parents=True, exist_ok=True)
    for kind in ("photo", "zone", "preview"):
        src = PHOTOS / f"{ref}-{kind}.jpg"
        if src.exists():
            dst = up / (f"{ref}.jpg" if kind == "photo" else f"{ref}-{kind}-demo.jpg")
            shutil.copyfile(src, dst)
            out[kind] = str(dst)
    if (PHOTOS / f"{ref}-outline.json").exists():
        out["outline"] = json.loads((PHOTOS / f"{ref}-outline.json").read_text(encoding="utf-8"))
    return out


def fill_geo() -> None:
    """Street shapes and street names need OpenStreetMap; fetch the missing ones (sample tickets, or a report made
    while offline). Started in a background thread so the server starts at once."""
    with SessionLocal() as s:
        for t in s.query(Ticket).filter(Ticket.lat.is_not(None)):
            if not (t.data or {}).get("street_name"):
                road = geo.place(t.lat, t.lng)[1]
                if road:
                    t.data = {**(t.data or {}), "street_name": road}
                    s.commit()
            if t.st >= 7:
                continue
            d = dict(t.data or {})
            zone = geo.shape_zone(d.get("zone"), t.lat, t.lng)
            rep = d.get("rep")
            if rep and rep.get("danger_zone"):
                rep = {**rep, "danger_zone": geo.shape_zone(rep["danger_zone"], t.lat, t.lng)}
            if zone != d.get("zone") or rep != d.get("rep"):
                t.data = {**d, "zone": zone, "rep": rep}
                s.commit()
