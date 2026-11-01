"""Addresses and street shapes from OpenStreetMap (Nominatim). Free service with a usage policy:
at most 1 request per second and an identifying User-Agent. For heavy use, run your own Nominatim."""
import json, logging, math, threading, time, urllib.parse, urllib.request

URL = "https://nominatim.openstreetmap.org"
HEADERS = {"User-Agent": "InfraSight/0.1 (municipal prototype)"}
_lock = threading.Lock()
_last = 0.0


def _get(path: str, **params) -> dict | list:
    global _last
    with _lock:                        # one request per second, across all users
        wait = _last + 1.1 - time.time()
        if wait > 0:
            time.sleep(wait)
        _last = time.time()
    q = urllib.parse.urlencode({"format": "jsonv2", **params})
    with urllib.request.urlopen(urllib.request.Request(f"{URL}/{path}?{q}", headers=HEADERS), timeout=10) as r:
        return json.load(r)


def _dist(a, b) -> float:
    """Metres between two [lat, lng] points."""
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12_742_000 * math.asin(math.sqrt(h))


def _lines(geojson: dict) -> list[list[list[float]]]:
    """GeoJSON (lng, lat) -> Leaflet polylines [[lat, lng], ...]."""
    t, c = geojson.get("type"), geojson.get("coordinates", [])
    if t == "LineString":
        return [[[y, x] for x, y in c]]
    if t == "MultiLineString":
        return [[[y, x] for x, y in line] for line in c]
    return []


def _city(a: dict) -> str | None:
    return a.get("city") or a.get("town") or a.get("village") or a.get("municipality")


def place(lat: float, lng: float) -> tuple[str | None, str | None]:
    """('12 Rue Colbert, Brest', 'Rue Colbert') for a map pin; the street name groups reports into hotspots."""
    try:
        a = _get("reverse", lat=lat, lon=lng, zoom=18, addressdetails=1).get("address", {})
    except Exception as e:
        logging.warning("Address lookup failed at %s,%s: %s", lat, lng, e)
        return None, None
    road = a.get("road") or a.get("pedestrian") or a.get("square")
    street = " ".join(x for x in (a.get("house_number"), road) if x)
    return ", ".join(x for x in (street, _city(a)) if x) or None, road


def address(lat: float, lng: float) -> str | None:
    return place(lat, lng)[0]


def distance(a, b) -> float:
    """Metres between two [lat, lng] points."""
    return _dist(a, b)


def street(lat: float, lng: float, reach_m: float) -> dict | None:
    """The street at the pin and every piece of it within reach_m: {"name": ..., "lines": [[[lat, lng], ...], ...]}.
    OpenStreetMap cuts a street into several pieces, so the pieces are found by searching the street name."""
    try:
        r = _get("reverse", lat=lat, lon=lng, zoom=17, polygon_geojson=1, addressdetails=1)
        if r.get("category") != "highway":
            return None
        lines, name, city = _lines(r.get("geojson", {})), r.get("name"), _city(r.get("address", {}))
        if name and city:
            for x in _get("search", street=name, city=city, polygon_geojson=1, limit=40):
                if x.get("category") == "highway" and x.get("osm_id") != r.get("osm_id"):
                    lines += [l for l in _lines(x.get("geojson", {})) if min(_dist((lat, lng), p) for p in l) <= reach_m]
        return {"name": name, "lines": lines} if lines else None
    except Exception as e:
        logging.warning("Street lookup failed at %s,%s: %s", lat, lng, e)
        return None


def shape_zone(zone: dict | None, lat: float | None, lng: float | None) -> dict | None:
    """Add the street shape to a 'street' danger zone (radius_m = length of street affected)."""
    if not zone or zone.get("shape") != "street" or lat is None or lng is None or zone.get("street"):
        return zone
    s = street(lat, lng, min(1000, max(150, zone.get("radius_m") or 0)))
    return {**zone, "street": s} if s else zone
