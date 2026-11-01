"""Sample tickets (and optional demo users) for an empty database. Enabled with SEED_DEMO=true."""
import logging
from datetime import datetime, timedelta
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
    dict(id=43, title="Streetlight out, Square Hugo", type="Lighting", addr="Square Hugo", owner="commune", st=1, sev=3,
         urg=3, cost=(350, 500), due=4, own=1, geo=(48.3912, -4.4830), age=6,
         desc="Light off for 6 nights. Pole intact. Path used by evening commuters.",
         zone={"shape": "point", "radius_m": 20, "level": 2, "description": "Dark path under the light"}),
    dict(id=44, title="Sunken manhole cover, RD 14", type="Roads", addr="Avenue Foch (RD 14)", owner="department", st=0,
         sev=4, urg=5, cost=(1800, 2200), due=-1, own=0, geo=(48.39245, -4.48755), age=0,
         desc="Cover sunken about 3 cm on a busy departmental road. Cars swerve.",
         cons={"danger_type": "Collision risk, traffic disrupted on RD 14", "blocked_access": False,
               "potential_events": [{"event": "Cars swerve into the oncoming lane", "likelihood": "medium",
                                     "impact": "Collision"}],
               "vulnerable_people": "Drivers, cyclists", "immediate_measures": ["Signage and speed limit", "Raise the cover"]},
         zone={"shape": "street", "radius_m": 200, "level": 4, "description": "RD 14 section around the cover"}),
    dict(id=45, title="Illegal dumping near market", type="Waste", addr="Place du Marché", owner="epci", st=1, sev=2,
         urg=2, cost=(600, 600), due=5, own=0, geo=(48.3904, -4.4861), age=9,
         desc="Bulky waste left on the pavement behind the market stalls."),
    dict(id=46, title="Cracked pavement, Rue Victor Hugo", type="Roads", addr="Rue Victor Hugo", owner="commune", st=3,
         sev=3, urg=2, cost=(18500, 22000), due=6, own=0, geo=(48.39070, -4.47852), age=15,
         desc="120 m of pavement cracked by tree roots. Pushchairs and wheelchairs blocked.",
         cons={"danger_type": "Pavement blocked for pushchairs and wheelchairs", "blocked_access": True,
               "potential_events": [{"event": "Users forced onto the roadway", "likelihood": "medium",
                                     "impact": "Collision risk with vehicles"}],
               "vulnerable_people": "Wheelchair users, parents with pushchairs",
               "immediate_measures": ["Mark a safe detour", "Fence off the worst sections"]},
         zone={"shape": "street", "radius_m": 120, "level": 3, "description": "120 m of cracked pavement"}),
    dict(id=38, title="Fallen branch on cycle path", type="Green spaces", addr="Allée du Parc", owner="commune", st=6,
         sev=2, urg=2, cost=(120, 120), due=3, own=1, geo=(48.3935, -4.4915), age=21,
         desc="Large branch blocking the cycle path after the storm. Removed; awaiting closure."),
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
STREETS = {42: "Rue des Lilas", 43: "Square Hugo", 44: "Avenue du Maréchal Foch", 45: "Place du Marché",
           46: "Rue Victor Hugo", 38: "Allée du Parc", 47: "Place de la Liberté"}
# closed reports of the past year: the history the hotspots are computed from
HISTORY = [
    dict(id=30, title="Pothole, Rue Victor Hugo", type="Roads", street="Rue Victor Hugo", geo=(48.39085, -4.47820),
         sev=3, cost=(900, 1200), age=45, desc="Pothole in the roadway after heavy rain."),
    dict(id=31, title="Pavement lifted by roots, Rue Victor Hugo", type="Roads", street="Rue Victor Hugo",
         geo=(48.39050, -4.47890), sev=3, cost=(3500, 4200), age=160, desc="Tree roots lifting the pavement slabs."),
    dict(id=32, title="Second pothole, Rue Victor Hugo", type="Roads", street="Rue Victor Hugo", geo=(48.39100, -4.47790),
         sev=2, cost=(600, 800), age=290, desc="Pothole at the edge of the road, near the bus stop."),
    dict(id=33, title="Pothole, Avenue du Maréchal Foch", type="Roads", street="Avenue du Maréchal Foch",
         geo=(48.39300, -4.48780), sev=4, cost=(1500, 2000), age=30, desc="Deep pothole in the right lane."),
    dict(id=34, title="Damaged drain, Avenue du Maréchal Foch", type="Water", street="Avenue du Maréchal Foch",
         geo=(48.39200, -4.48740), sev=3, cost=(2500, 3000), age=210, desc="Drain grate broken, water pools after rain."),
]
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
            s.add(Ticket(ref=f"IS-{x['id']:04d}", id=x["id"], title=x["title"], type=x["type"], addr=x["addr"],
                         owner=x["owner"], reporter_id=citizen.id if citizen and x["own"] else None, desc=x["desc"],
                         lat=x["geo"][0], lng=x["geo"][1], st=x["st"], sev=x["sev"], urg=x["urg"], due=x["due"],
                         cost_min=x["cost"] and x["cost"][0], cost_max=x["cost"] and x["cost"][1], created=now - timedelta(days=x["age"]),
                         image_path=None, data={"cons": x.get("cons"), "zone": x.get("zone"), "rep": None, "ai": {}, "ch": ch,
                                                "street_name": STREETS.get(x["id"])},
                         audit=[Audit(d="Opened", w="Citizen portal", e="Report received and registered")]))
        for x in HISTORY:                  # also added to an older demo database
            if s.get(Ticket, f"IS-{x['id']:04d}"):
                continue
            s.add(Ticket(ref=f"IS-{x['id']:04d}", id=x["id"], title=x["title"], type=x["type"], addr=x["street"],
                         owner="commune", reporter_id=None, desc=x["desc"], lat=x["geo"][0], lng=x["geo"][1], st=7,
                         sev=x["sev"], urg=x["sev"], due=0, cost_min=x["cost"][0], cost_max=x["cost"][1],
                         created=now - timedelta(days=x["age"]), image_path=None,
                         data={"rep": None, "ai": {}, "ch": {}, "street_name": x["street"]},
                         audit=[Audit(d="Archive", w="Citizen portal", e="Report received, repaired and closed")]))
        s.commit()


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
