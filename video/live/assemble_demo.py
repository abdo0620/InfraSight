"""Turns the recorded take (record_demo.py) into the live demo video: one continuous take, with English captions saying
which Meta model powers each step.

Time: the take is in slow motion (events.json "slow"), so by default it plays back that many times faster, which is real
speed on screen. Live AI calls (recorded at their real speed) are shortened to at most AI_MAX seconds and labelled with
their real duration; typing and page loads are sped up and labelled; moments where nothing at all moves (no new frame,
no pointer movement) are shortened. Every caption stays on screen long enough to be read. The length is fitted to
exactly TARGET seconds.

The pointer is drawn here, at 30 frames a second, from the positions the recorder logged.
Usage: python live/assemble_demo.py <recording dir> <output mp4> <ffmpeg> <target seconds>"""
import bisect, io, json, math, subprocess, sys, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REC, OUT, FFMPEG = Path(sys.argv[1]), sys.argv[2], str(Path(sys.argv[3]).resolve())
TARGET = float(sys.argv[4])
FPS = 30
AI_MAX, AI_MIN = 5.0, 2.5                                       # seconds on screen for one live AI call

rec = json.load(open(REC / "frames.json"))
ev = json.load(open(REC / "events.json"))
t0, t1, stamps = rec["t0"], rec["t1"], rec["frames"]
SCALE = rec.get("scale", 1.5)
W, H = int(1280 * SCALE), int(720 * SCALE)
U = W / 1920                                                    # overlay sizes were designed for 1920 wide
SLOW = ev.get("slow", 1.0)
caps = sorted(ev["captions"])
# shorter captions for the final film (same meaning), keyed by how the recorded caption starts
SHORT = {
    "Live demo, recorded": "Live demo, recorded in one take: the real InfraSight app, calling Meta's models through the Meta Model API.",
    "Everything shown was built": "Everything shown was built this hackathon week. Long AI calls are sped up, and the top-right corner says so.",
    "A citizen signs in": "A citizen signs in. Every report is pinned on the map: type an address, pick an OpenStreetMap suggestion.",
    "They add one photo": "Then one photo and one sentence in their own words. No form, no category to choose.",
    "When they send it": "Muse Spark reads photo and text together: the problem, severity, urgency, who owns the street, duplicates nearby.",
    "Then SAM 3.1 outlines": "Then SAM 3.1 outlines the damage, and Muse Image draws the street once repaired.",
    "The repair picture": "The repair picture is always labelled as an illustration, never passed off as a photo.",
    "A second citizen": "A second citizen reports the same shelter. Muse Spark matches it to the open case and merges them: one case, two followers.",
    "Each citizen picks": "Each citizen picks their language, here Spanish. Muse Spark writes them an update at every step of the repair.",
    "The town hall's technician": "The town hall's technician sees every case on the map: severity, AI danger zones, detours, recurring hotspots.",
    "On the ticket": "On the ticket, a before / after slider compares the photo with Muse Image's repair preview, next to the SAM 3.1 outline.",
    "'Outline and measure": "'Outline and measure the damage': SAM 3.1 outlines it, then Muse Spark estimates its real size from the kerb and road markings.",
    "'Generate full report'": "'Generate full report': Muse Spark names the responsible authority, the procurement route and the legal articles, or [verify].",
    "Costs are not invented": "Costs are not invented: Muse Spark lists the work, and the server prices each line from public price schedules, with sources.",
    "Every repair follows": "Every repair follows 7 legal stages. Muse Spark drafts the documents of the current one: here the decision memo.",
    "If the street must close": "If the street must close, InfraSight computes the shortest legal detour on the OpenStreetMap road network.",
    "Muse Spark then drafts": "Muse Spark drafts the mayor's traffic order with that detour. The dates and the order number stay [to fill].",
    "Elected officials": "Elected officials get a dashboard of priorities, deadlines and budget, and a weekly brief written by Muse Spark.",
    "Hotspots are streets": "Hotspots are streets where problems keep coming back. With no history yet, Muse Spark says so instead of inventing a risk.",
    "Every case exports": "Every case exports as a PDF report: images, sources, cost, the 7 stages, the detour and the traffic order.",
    "Three Meta models": "Three Meta models, one real product: Muse Spark, SAM 3.1 and Muse Image.  github.com/abdo0620/InfraSight",
}
caps = [[t, next((v for k, v in SHORT.items() if c.startswith(k)), c)] for t, c in caps]
if not ev.get("merged", True):                                  # the merge subtitle is only true if Muse Spark merged
    caps = [[t, "A second citizen reports the same bus shelter. Muse Spark compares it with the open cases nearby; "
                "here it kept it as a separate case, which staff can still merge by hand."
             if c.startswith("A second citizen") else c] for t, c in caps]
cursor = ev.get("cursor", [])
cur_t = [c[0] for c in cursor]
clicks = ev.get("clicks", [])


def read_time(text):
    """Seconds a caption needs on screen."""
    return min(8.0, max(3.5, 0.8 + len(text.split()) / 4.0))


# ---- the pieces of the take, in real time: [start, end, kind, label]
spans = []
for a, b, kind, label, *pace in ev["speed"]:
    # the last fields: the real duration of the whole span, and the slow-motion factor it was recorded at
    spans.append([a, b, kind, label, b - a, pace[0] if pace else SLOW])
# an AI speed-up starts only once the caption shown just before it has been read (at real speed)
for s in spans:
    if s[2] != "ai":
        continue
    for t, c in caps:
        if t <= s[0] and s[0] < t + read_time(c) * SLOW:
            s[0] = min(t + read_time(c) * SLOW, s[1])
spans = [s for s in spans if s[1] - s[0] > 1.0]                 # a call already over by then plays at real speed
holds = [tuple(h) for h in ev["hold"]]


def moving(a, b):
    """Is anything moving between real times a and b: a new frame or the pointer?"""
    i = bisect.bisect_right(stamps, a)
    if i < len(stamps) and stamps[i] < b:
        return True
    j = bisect.bisect_right(cur_t, a)
    return j < len(cur_t) and cur_t[j] < b


# still stretches (outside spans and holds): nothing changes on screen for more than 0.6 s of video -> cut short.
# idle stretches: the hand does not move the pointer for more than 1.2 s (typing, a page loading, waiting) -> 3x, labelled.
# The pointer's own movements are never sped up.
still, idle = [], []
marks = sorted(set(stamps + cur_t + [t0, t1]))
free = lambda a, b: not any(s[0] < b and a < s[1] for s in spans) and not any(h0 < b and a < h1 for h0, h1 in holds)
for a, b in zip(marks, marks[1:]):
    if b - a > 0.6 * SLOW and free(a, b):
        still.append([a + 0.25 * SLOW, b - 0.02])
moves = sorted(set(cur_t + [t0, t1]))
for a, b in zip(moves, moves[1:]):
    a2, b2 = a + 0.35 * SLOW, b - 0.3 * SLOW
    if b2 - a2 > 0.9 * SLOW:
        # split around holds and spans, keep the free parts
        cuts = sorted([(max(a2, s[0]), min(b2, s[1])) for s in spans if s[0] < b2 and a2 < s[1]] +
                      [(max(a2, h0), min(b2, h1)) for h0, h1 in holds if h0 < b2 and a2 < h1])
        cur = a2
        for c0, c1 in cuts + [(b2, b2)]:
            if c0 - cur > 0.9 * SLOW:
                idle.append([cur, c0])
            cur = max(cur, c1)
IDLE = 3.0


def timeline(k):
    """Segments [a, b, real seconds per video second, label] for a tightness k (1 = the default lengths, smaller =
    shorter AI calls, typing and holds), then the protection of caption reading time."""
    segs = []
    for a, b, kind, label, whole, pace in spans:
        real = b - a
        if kind == "ai":
            ncap = sum(1 for t, _ in caps if a < t < b)
            out = min(AI_MAX, max(AI_MIN, real / 6)) if not ncap else AI_MAX
            out = max(AI_MIN, min(out, AI_MAX * max(k, 0.5))) if k < 1 and not ncap else out
            segs.append([a, b, real / out, f"{real / out:.0f}x  ·  live AI call sped up  ·  {whole:.0f} s in real time", kind, SLOW])
        else:
            natural = real / pace
            out = min(natural, max(2.5, min(6.0, natural / 5)) * min(1.0, k))
            segs.append([a, b, real / out, f"{natural / out:.0f}x  ·  sped up", kind, pace])
    for a, b in still:
        segs.append([a, b, (b - a) / 0.05, None, "still", SLOW])
    f_idle = min(5.0, IDLE / max(k, 0.6))
    for a, b in idle:                                           # (overlaps with still stretches: the first one wins)
        segs.append([a, b, f_idle * SLOW, f"{f_idle:.0f}x  ·  sped up", "idle", SLOW])
    if k < 1:                                                   # tighter: holds lose up to 45 %
        for h0, h1 in holds:
            cut = (h1 - h0) * min(0.45, 1 - k)
            segs.append([h1 - cut, h1, 1e6, None, "cut", SLOW])
    # split the speed-ups at every caption, so the reading time of each caption can be given back where it is shown
    ct = [t for t, _ in caps]
    split = []
    for sg in segs:
        if sg[4] in ("idle", "still", "ui", "cut"):
            inner = [t for t in ct if sg[0] < t < sg[1]]
            edges = [sg[0]] + inner + [sg[1]]
            for x0, x1 in zip(edges, edges[1:]):
                split.append([x0, x1] + sg[2:])
        else:
            split.append(sg)
    segs = split
    segs.sort()
    clean, last = [], t0
    for s in segs:
        if s[0] >= last and s[1] > s[0]:
            clean.append(s)
            last = s[1]
    return clean


def points_of(segs):
    pts, at, cur = [(t0, 0.0)], 0.0, t0
    for a, b, r, *_ in segs:
        at += (a - cur) / SLOW
        pts.append((a, at))
        at += (b - a) / r
        pts.append((b, at))
        cur = b
    at += (t1 - cur) / SLOW
    pts.append((t1, at))
    return pts


def out_at(pts, t):
    reals = [p[0] for p in pts]
    i = max(0, min(bisect.bisect_right(reals, t) - 1, len(pts) - 2))
    (ra, oa), (rb, ob) = pts[i], pts[i + 1]
    return oa if rb == ra else oa + (t - ra) * (ob - oa) / (rb - ra)


def protect(segs):
    """Every caption gets its reading time: between a caption and the next, give back time first from the still
    stretches, then from the typing speed-ups."""
    for _ in range(4):
        pts = points_of(segs)
        changed = False
        for (ta, ca), (tb, _) in zip(caps, caps[1:]):
            need = read_time(ca) - (out_at(pts, tb) - out_at(pts, ta))
            if need <= 0.05:
                continue
            for kind in ("still", "idle", "ui", "cut"):
                for s in segs:
                    if need <= 0.05 or s[4] != kind or not (ta <= s[0] < tb):
                        continue
                    cur_out = (s[1] - s[0]) / s[2]
                    max_out = (s[1] - s[0]) / s[5]
                    add = min(need, max_out - cur_out)
                    if add > 0.01:
                        s[2] = (s[1] - s[0]) / (cur_out + add)
                        if s[3] and s[4] in ("ui", "idle"):
                            f = (s[1] - s[0]) / s[5] / (cur_out + add)
                            s[3] = f"{f:.0f}x  ·  sped up" if f >= 1.5 else None
                        need -= add
                        changed = True
        if not changed:
            break
    return segs


lo, hi = 0.3, 1.0
segs = protect(timeline(1.0))
if points_of(segs)[-1][1] > TARGET:
    for _ in range(25):
        k = (lo + hi) / 2
        if points_of(protect(timeline(k)))[-1][1] > TARGET:
            hi = k
        else:
            lo = k
    segs = protect(timeline(lo))
points = points_of(segs)
reals, outs = [p[0] for p in points], [p[1] for p in points]
length = outs[-1]
if length > TARGET + 0.01:
    print(f"WARNING: {length:.1f} s even at the tightest setting; cut to {TARGET} s")
N = int(round(TARGET * FPS))


def real_at(o):
    i = max(0, min(bisect.bisect_right(outs, o) - 1, len(outs) - 2))
    (ra, oa), (rb, ob) = points[i], points[i + 1]
    return ra if ob == oa else ra + (o - oa) * (rb - ra) / (ob - oa)


def seg_at(t):
    for s in segs:
        if s[0] <= t < s[1]:
            return s
    return None


def cursor_at(t):
    if not cursor:
        return None
    i = bisect.bisect_right(cur_t, t) - 1
    if i < 0:
        return cursor[0][1], cursor[0][2]
    if i >= len(cursor) - 1:
        return cursor[-1][1], cursor[-1][2]
    (ta, xa, ya), (tb, xb, yb) = cursor[i], cursor[i + 1]
    if tb - ta > 0.5 * SLOW:                                    # the pointer was resting: no interpolation across the pause
        return xa, ya
    u = (t - ta) / (tb - ta) if tb > ta else 0
    return xa + (xb - xa) * u, ya + (yb - ya) * u


click_out = [(out_at(points, c[0]), c[1], c[2]) for c in clicks]

# the speed badge, in video time: labels closer than 0.8 s are merged (the stronger one wins), and each stays at least
# 1.2 s on screen, so the badge never flickers
badges = []
for a, b, r, label, *_ in segs:
    if not label:
        continue
    oa, ob = out_at(points, a), out_at(points, b)
    if badges and oa - badges[-1][1] < 0.8:
        prev = badges[-1]
        strong = label if ("AI" in label or "AI" not in prev[2]) and not ("AI" in prev[2]) else prev[2]
        if "AI" in label:
            strong = label
        badges[-1] = [prev[0], max(prev[1], ob), strong]
    else:
        badges.append([oa, ob, label])
for bd in badges:
    bd[1] = max(bd[1], bd[0] + 1.2)
merged_b = []
for bd in badges:                                               # again, after the extension
    if merged_b and bd[0] - merged_b[-1][1] < 0.6:
        prev = merged_b[-1]
        merged_b[-1] = [prev[0], max(prev[1], bd[1]), bd[2] if "AI" in bd[2] or "AI" not in prev[2] else prev[2]]
    else:
        merged_b.append(bd)
badges = merged_b


def badge_at(o):
    for oa, ob, label in badges:
        if oa <= o < ob:
            return label
    return None

# ---- drawing
F = "C:/Windows/Fonts/"
CAP = ImageFont.truetype(F + "seguisb.ttf", round(36 * U))
BADGE = ImageFont.truetype(F + "seguisb.ttf", round(26 * U))


def pointer_sprite(size):
    """A classic arrow pointer, white with a dark outline, drawn 4x larger then scaled down for smooth edges."""
    k = 4
    pts = [(1, 1), (1, 16), (5, 12.3), (8, 19), (10.6, 17.9), (7.7, 11.3), (13.2, 11.3)]
    s = size * k / 20
    im = Image.new("RGBA", (int(16 * s) + 8, int(21 * s) + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    poly = [(x * s + 4, y * s + 4) for x, y in pts]
    d.polygon(poly, fill=(255, 255, 255, 255), outline=(17, 17, 17, 255), width=int(1.3 * k * size / 20 * 1.6))
    im = im.resize((im.width // k, im.height // k), Image.LANCZOS)
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    shadow.putalpha(im.getchannel("A").point(lambda a: a * 0.45))
    return im, shadow


POINTER = {sc: pointer_sprite(24 * SCALE * sc) for sc in (1.0, 0.86)}


def pill(d, xy, text, font, fill=(10, 10, 12, 205), ink=(244, 244, 245), dot=None):
    x, y = xy
    pad = (round(22 * U), round(12 * U))
    tw = d.textlength(text, font=font)
    extra = round(30 * U) if dot else 0
    box = [x, y, x + tw + 2 * pad[0] + extra, y + font.size + 2 * pad[1] + round(4 * U)]
    d.rounded_rectangle(box, radius=(box[3] - box[1]) // 2, fill=fill, outline=(255, 255, 255, 40), width=1)
    if dot:
        cy, r = (box[1] + box[3]) // 2, round(7 * U)
        d.ellipse([x + pad[0], cy - r, x + pad[0] + 2 * r, cy + r], fill=dot)
    d.text((x + pad[0] + extra, y + pad[1] - round(2 * U)), text, font=font, fill=ink)
    return box


def overlay(img, t, o):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # click ripples (in video time), then the pointer
    press = False
    for oc, cx, cy in click_out:
        age = o - oc
        if 0 <= age < 0.45:
            p = age / 0.45
            r = (10 + 22 * p) * SCALE
            a = int(230 * (1 - p) ** 1.5)
            d.ellipse([cx * SCALE - r, cy * SCALE - r, cx * SCALE + r, cy * SCALE + r], outline=(217, 119, 87, a), width=max(2, round(3 * SCALE)))
        if -0.04 <= age < 0.1:
            press = True
    pos = cursor_at(t)
    if pos:
        sprite, shadow = POINTER[0.86 if press else 1.0]
        px, py = int(pos[0] * SCALE) - 4, int(pos[1] * SCALE) - 4
        ov.alpha_composite(shadow, (px + round(2 * SCALE), py + round(3 * SCALE)))
        ov.alpha_composite(sprite, (px, py))
    pill(d, (round(36 * U), round(30 * U)), "LIVE  ·  the real app  ·  real Meta model API calls", BADGE, dot=(239, 68, 68))
    label = badge_at(o)
    if label:
        tw = d.textlength(label, font=BADGE)
        pill(d, (W - tw - round(110 * U), round(30 * U)), label, BADGE, fill=(217, 119, 87, 230), ink=(28, 14, 8), dot=(28, 14, 8))
    text = None
    for ct, c in caps:
        if ct <= t:
            text = c
    if text:
        lines = textwrap.wrap(text, 70)
        lh = CAP.size + round(14 * U)
        bh = lh * len(lines) + round(34 * U)
        widest = max(d.textlength(l, font=CAP) for l in lines)
        x0, y0 = (W - widest) / 2 - round(36 * U), H - round(60 * U) - bh
        d.rounded_rectangle([x0, y0, x0 + widest + round(72 * U), y0 + bh], radius=round(22 * U), fill=(10, 10, 12, 215),
                            outline=(217, 119, 87, 160), width=max(2, round(2 * U)))
        for i, l in enumerate(lines):
            lw = d.textlength(l, font=CAP)
            d.text(((W - lw) / 2, y0 + round(15 * U) + i * lh), l, font=CAP, fill=(244, 244, 245))
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


if "--plan" in sys.argv:                                        # print the plan only
    print(f"length {length:.1f} s -> {TARGET} s")
    pts = points
    for (ta, ca), (tb, _) in zip(caps, caps[1:] + [[t1, ""]]):
        print(f"  {out_at(pts, ta):6.1f} s  {out_at(pts, tb) - out_at(pts, ta):4.1f} s on screen  {ca[:70]}")
    for oa, ob, label in badges:
        print(f"  {oa:6.1f}-{ob:6.1f} s  {label}")
    sys.exit()

frames = sorted((REC / "frames").glob("*.jpg"))
enc = subprocess.Popen([FFMPEG, "-v", "error", "-y", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", str(FPS),
                        "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-pix_fmt", "yuv420p",
                        "-r", str(FPS), "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
cache = (None, None)
for k in range(N):
    o = min(k / FPS, length - 1e-6)                             # past the end of the take: hold the last frame
    t = real_at(o)
    i = max(0, bisect.bisect_right(stamps, t) - 1)
    if cache[0] != i:
        im = Image.open(frames[i]).convert("RGB")
        cache = (i, im if im.size == (W, H) else im.resize((W, H), Image.LANCZOS))
    buf = io.BytesIO()
    overlay(cache[1], t, o).save(buf, "JPEG", quality=95)
    enc.stdin.write(buf.getvalue())
enc.stdin.close()
enc.wait()
print(f"{OUT}: {N / FPS:.2f} s ({N} frames) from a {t1 - t0:.1f} s take; natural length {length:.1f} s")
