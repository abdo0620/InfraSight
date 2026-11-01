"""Detour around a blocked street section, computed here from the OpenStreetMap road network (Overpass API):
download the drivable roads around the section, drop the blocked pieces, shortest path between its two ends."""
import heapq, json, logging, math, urllib.parse, urllib.request
from collections import defaultdict
from ..config import settings
from .geo import HEADERS, distance

DRIVABLE = ("motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street|service|"
            "motorway_link|trunk_link|primary_link|secondary_link|tertiary_link")
MARGIN = 0.006                         # degrees around the section, about 450-650 m
ON_STREET_M = 10                       # a road piece this close to the blocked lines (both ends) is blocked


def _overpass(query: str) -> dict:
    last = None
    for url in settings.overpass_urls:  # public servers are often busy: try each in turn
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": query}).encode(), headers=HEADERS)
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception as e:
            logging.warning("Overpass %s failed: %s", url, e)
            last = e
    raise RuntimeError(f"No road data service answered ({last}). Check OVERPASS_URLS in backend/.env.")


def _seg_dist(p, a, b) -> float:
    """Metres from point p to segment a-b (flat approximation, fine at street scale)."""
    k = math.cos(math.radians(p[0])) * 111_320
    ax, ay, bx, by = (a[1] - p[1]) * k, (a[0] - p[0]) * 111_320, (b[1] - p[1]) * k, (b[0] - p[0]) * 111_320
    dx, dy = bx - ax, by - ay
    t = 0 if dx == dy == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / (dx * dx + dy * dy)))
    return math.hypot(ax + t * dx, ay + t * dy)


def _on(p, lines) -> bool:
    return any(_seg_dist(p, l[i], l[i + 1]) <= ON_STREET_M for l in lines for i in range(len(l) - 1))


def _ends(lines):
    """The two ends of the blocked section: the pair of line ends farthest apart."""
    ends = [p for l in lines for p in (l[0], l[-1])]
    return max(((a, b) for i, a in enumerate(ends) for b in ends[i + 1:]), key=lambda ab: distance(*ab))


def detour(lines: list[list[list[float]]]) -> dict:
    """{"lines": [[[lat, lng], ...]], "length_m", "streets": [names in driving order], "from", "to"}."""
    pts = [p for l in lines for p in l]
    s, w = min(p[0] for p in pts) - MARGIN, min(p[1] for p in pts) - MARGIN
    n, e = max(p[0] for p in pts) + MARGIN, max(p[1] for p in pts) + MARGIN
    data = _overpass(f'[out:json][timeout:60];way["highway"~"^({DRIVABLE})$"]["access"!~"^(no|private)$"]'
                     f'({s:.6f},{w:.6f},{n:.6f},{e:.6f});out body geom;')
    coord, graph = {}, defaultdict(list)
    for way in data.get("elements", []):
        if way.get("type") != "way" or "geometry" not in way:
            continue
        tags = way.get("tags", {})
        for nid, g in zip(way["nodes"], way["geometry"]):
            coord[nid] = (g["lat"], g["lon"])
        ow = tags.get("oneway") or ("yes" if tags.get("junction") in ("roundabout", "circular") else "no")
        name = tags.get("name") or tags.get("ref") or ""
        for a, b in zip(way["nodes"], way["nodes"][1:]):
            pa, pb = coord[a], coord[b]
            mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
            if _on(pa, lines) and _on(pb, lines) and _on(mid, lines):
                continue                # the blocked section itself
            d = distance(pa, pb)
            if ow != "-1":
                graph[a].append((b, d, name))
            if ow not in ("yes", "true", "1"):
                graph[b].append((a, d, name))
    if not graph:
        raise RuntimeError("No roads found around the blocked section")
    targets = {b for edges in graph.values() for b, _, _ in edges}
    a_pt, b_pt = _ends(lines)
    src = min(graph, key=lambda k: distance(coord[k], a_pt))
    dst = min(targets, key=lambda k: distance(coord[k], b_pt))
    path = _shortest(graph, src, dst) or _shortest(graph, dst, src)   # one-way streets: try the other direction
    if not path:
        raise RuntimeError("No detour found around the blocked section")
    streets = []
    for _, name in path[1:]:
        if name and (not streets or streets[-1] != name):
            streets.append(name)
    nodes = [nid for nid, _ in path]
    line = [list(coord[k]) for k in nodes]
    return {"lines": [line], "length_m": round(sum(distance(line[i], line[i + 1]) for i in range(len(line) - 1))),
            "streets": streets, "from": line[0], "to": line[-1]}


def _shortest(graph, src, dst):
    """Dijkstra. Returns [(node, street name used to reach it), ...] or None."""
    dist, prev, heap = {src: 0.0}, {}, [(0.0, src)]
    while heap:
        d, k = heapq.heappop(heap)
        if k == dst:
            break
        if d > dist.get(k, math.inf):
            continue
        for nxt, w, name in graph.get(k, ()):
            nd = d + w
            if nd < dist.get(nxt, math.inf):
                dist[nxt], prev[nxt] = nd, (k, name)
                heapq.heappush(heap, (nd, nxt))
    if dst not in dist or src == dst:
        return None
    path, k = [], dst
    while k != src:
        k_prev, name = prev[k]
        path.append((k, name))
        k = k_prev
    return [(src, "")] + path[::-1]
