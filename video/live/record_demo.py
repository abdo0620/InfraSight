"""Records a live demo of the real InfraSight app, in one take: a real browser drives the running app (real clicks, real
typing, real Meta model calls) while the browser's screencast captures every screen update. Nothing is staged or recreated.

Smooth motion: headless (software) rendering of the app at 1920 x 1080 delivers only 2 to 7 frames a second, far too
few for smooth scrolling and transitions. So the take is recorded in slow motion: the page's CSS animations run SLOW times slower (DevTools
Animation.setPlaybackRate) and every scroll, drag and pause of the script lasts SLOW times longer; the assembler plays the
take back SLOW times faster, which gives SLOW times more frames per second of motion. Live AI calls are not slowed: they
run at their real speed and are shown sped up, with their real duration on screen.

The mouse pointer is not part of the page: the script moves the real mouse along human-like paths (curved, eased,
slight overshoot, a short pause before each click) and logs every position, and the assembler draws the pointer at a
true 30 frames a second.

Writes <out>/frames/*.jpg, <out>/frames.json (timestamps), <out>/events.json (captions, sped-up spans, held results,
pointer path, clicks, SLOW).
Usage: python live/record_demo.py <app url> <out dir> <photo> <second photo>"""
import base64, json, math, queue, random, shutil, subprocess, sys, threading, time, urllib.request
from pathlib import Path
import websocket

URL, OUT = sys.argv[1].rstrip('/'), Path(sys.argv[2])
PHOTO, PHOTO2 = Path(sys.argv[3]).resolve(), Path(sys.argv[4]).resolve()
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
import os
W, H = 1280, 720                                                  # CSS viewport
SCALE = float(os.environ.get("REC_SCALE", "1.5"))                 # true device pixels: frames come out at 1920 x 1080
SLOW = float(os.environ.get("REC_SLOW", "10"))                    # slow-motion factor of the take (see above)
PACE = [SLOW]                                                     # 1 inside the sped-up spans: no need for slow motion there
now = time.time
rnd = random.Random(7)


class CDP:
    """DevTools client. The reader thread acks each screencast frame at once (so the browser keeps sending at full rate)
    and hands it to a writer thread; replies to commands are routed back to the waiting caller."""

    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=300, max_size=None)
        self.n, self.lock, self.wait, self.res = 0, threading.Lock(), {}, {}
        self.frames, self.recording, self.q = [], False, queue.Queue()
        (OUT / "frames").mkdir(parents=True, exist_ok=True)
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._write, daemon=True).start()

    def _read(self):
        while True:
            try:
                m = json.loads(self.ws.recv())
            except Exception:
                return
            if "id" in m and m["id"] in self.wait:
                self.res[m["id"]] = m
                self.wait.pop(m["id"]).set()
            elif m.get("method") == "Page.screencastFrame":
                p = m["params"]
                self.send("Page.screencastFrameAck", wait=False, sessionId=p["sessionId"])
                if self.recording:
                    self.q.put((p["metadata"]["timestamp"], p["data"]))

    def _write(self):
        while True:
            ts, data = self.q.get()
            i = len(self.frames)
            (OUT / "frames" / f"{i:06d}.jpg").write_bytes(base64.b64decode(data))
            self.frames.append(ts)
            self.q.task_done()

    def send(self, method, wait=True, **params):
        with self.lock:
            self.n += 1
            i = self.n
            ev = threading.Event()
            if wait:
                self.wait[i] = ev
            self.ws.send(json.dumps({"id": i, "method": method, "params": params}))
        if not wait:
            return None
        ev.wait(300)
        return self.res.pop(i, {}).get("result", {})

    def js(self, expr):
        r = self.send("Runtime.evaluate", expression=expr, awaitPromise=True, returnByValue=True)
        return r.get("result", {}).get("value")


EVENTS = {"captions": [], "speed": [], "hold": [], "cursor": [], "clicks": [], "slow": SLOW}
LAST = {"cap": 0.0, "fast": False}


def nap(seconds):
    """A pause of the script, in seconds of the finished video (the take is in slow motion)."""
    time.sleep(seconds * PACE[0])


def caption(text, min_gap=5.0):
    """Show a subtitle; at real speed, the previous one stays at least min_gap seconds (of video) so it can be read."""
    if not LAST["fast"]:
        wait = LAST["cap"] + min_gap * SLOW - now()
        if wait > 0:
            time.sleep(wait)
    EVENTS["captions"].append([now(), text])
    LAST["cap"] = now()
    print(f"[{now() - T0:6.1f}] {text[:90]}", flush=True)


class fast:
    """A span shown sped up in the video, and labelled so ("ui": typing and page loads; "ai": a live AI call)."""

    def __init__(self, kind, label):
        self.kind, self.label = kind, label

    def __enter__(self):
        self.outer = LAST["fast"]
        if self.outer:                                                # already inside a sped-up span: nothing to log
            return
        self.t0, LAST["fast"] = now(), True
        PACE[0] = 1.0

    def __exit__(self, *a):
        if self.outer:
            return
        EVENTS["speed"].append([self.t0, now(), self.kind, self.label, PACE[0]])
        LAST["fast"] = False
        PACE[0] = SLOW
        print(f"   {self.label}: {now() - self.t0:.1f} s real", flush=True)


def hold(seconds):
    """Stay on a result; the video keeps it at real speed for `seconds`."""
    t = now()
    nap(seconds)
    EVENTS["hold"].append([t, now()])


# ---- the pointer: human-like movement ---------------------------------------------------------------------------
CUR = [1180.0, 640.0]


def _send_mouse(x, y, buttons=0):
    cdp.send("Input.dispatchMouseEvent", wait=False, type="mouseMoved", x=x, y=y, button="left" if buttons else "none", buttons=buttons)
    EVENTS["cursor"].append([now(), round(x, 2), round(y, 2)])


def _stroke(x1, y1, dur, buttons=0, curve=True):
    """One stroke from the current position: a gently curved path (a quadratic Bezier with its control point off to one
    side), a minimum-jerk speed profile (slow start, fast middle, slow landing) and a faint hand tremor."""
    x0, y0 = CUR
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy)
    if d < 1:
        return
    nx, ny = -dy / d, dx / d
    bend = rnd.uniform(0.06, 0.16) * d * rnd.choice((-1, 1)) if curve else 0.0
    f = rnd.uniform(0.35, 0.6)
    cx, cy = x0 + dx * f + nx * bend, y0 + dy * f + ny * bend
    ph1, ph2 = rnd.uniform(0, 6.3), rnd.uniform(0, 6.3)
    t0, real = now(), dur * PACE[0]
    while True:
        u = min(1.0, (now() - t0) / real)
        s = u * u * u * (10 - 15 * u + 6 * u * u)
        bx = (1 - s) ** 2 * x0 + 2 * (1 - s) * s * cx + s * s * x1
        by = (1 - s) ** 2 * y0 + 2 * (1 - s) * s * cy + s * s * y1
        amp = 0.6 * math.sin(math.pi * u)                         # tremor fades out on landing
        _send_mouse(bx + amp * math.sin(u * 23 + ph1), by + amp * math.sin(u * 19 + ph2), buttons)
        if u >= 1:
            break
        time.sleep(1 / 90 * PACE[0])
    CUR[0], CUR[1] = x1, y1


def move(x, y, buttons=0):
    """Move like a hand: duration from Fitts' law, a small overshoot and correction on long moves."""
    d = math.hypot(x - CUR[0], y - CUR[1])
    if d < 2:
        return
    dur = (0.17 + 0.1 * math.log2(1 + d / 24)) * rnd.uniform(0.9, 1.12)
    if d > 220:
        over = rnd.uniform(0.02, 0.045) * d
        ux, uy = (x - CUR[0]) / d, (y - CUR[1]) / d
        _stroke(x + ux * over + rnd.uniform(-4, 4), y + uy * over + rnd.uniform(-4, 4), dur * 0.86, buttons)
        _stroke(x, y, rnd.uniform(0.13, 0.19), buttons, curve=False)
    else:
        _stroke(x, y, dur, buttons)


def click_at(x, y):
    move(x, y)
    nap(rnd.uniform(0.07, 0.14))                                 # aim settles before the press
    cdp.send("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button="left", buttons=1, clickCount=1)
    EVENTS["clicks"].append([now(), x, y])
    nap(rnd.uniform(0.06, 0.09))
    cdp.send("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left", buttons=0, clickCount=1)
    nap(0.25)


def drift():
    """After starting something, the hand moves the pointer a little out of the way."""
    move(min(W - 30, max(30, CUR[0] + rnd.uniform(60, 140) * rnd.choice((-1, 1)))), min(H - 30, max(30, CUR[1] + rnd.uniform(40, 110))))


# ---- page helpers -----------------------------------------------------------------------------------------------
SCROLL_JS = r"""window.__scrollTo=(y,ms)=>new Promise(r=>{const y0=scrollY,t0=performance.now();const D=y-y0;if(Math.abs(D)<2)return r();
const e=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;(function f(){const t=Math.min(1,(performance.now()-t0)/ms);scrollTo(0,y0+D*e(t));t<1?requestAnimationFrame(f):r()})()})"""

FIND_JS = r"""((q,text)=>{const els=[...document.querySelectorAll(q)].filter(e=>e.offsetParent!==null&&(!text||e.textContent.trim().includes(text)));
const e=els[0];if(!e)return null;const r=e.getBoundingClientRect();return {x:r.left+r.width/2,y:r.top+r.height/2,w:r.width,h:r.height,l:r.left,t:r.top,sy:scrollY}})"""


def smooth_scroll(y, seconds=None):
    cdp.js(SCROLL_JS)
    cur = cdp.js("scrollY") or 0
    if seconds is None:
        seconds = min(1.3, 0.45 + abs(y - cur) / 1400)
    cdp.js(f"window.__scrollTo({max(0, y)},{seconds * PACE[0] * 1000:.0f})")
    nap(0.15)


def where(sel, text="", tries=80):
    for _ in range(tries):
        p = cdp.js(f"{FIND_JS}({json.dumps(sel)},{json.dumps(text)})")
        if p:
            if p["t"] < 60 or p["t"] + p["h"] > H - 20:                   # off screen: scroll to it smoothly, then measure
                smooth_scroll(p["sy"] + p["t"] - H * 0.35)
                p = cdp.js(f"{FIND_JS}({json.dumps(sel)},{json.dumps(text)})") or p
            return p
        time.sleep(0.25)
    raise RuntimeError(f"not found: {sel} {text}")


def click(sel, text=""):
    p = where(sel, text)
    # not dead centre: people click somewhere on the button
    x = p["x"] + rnd.uniform(-0.22, 0.22) * min(p["w"], 60)
    y = p["y"] + rnd.uniform(-0.18, 0.18) * min(p["h"], 24)
    click_at(x, y)


def type_text(text, delay=0.05):
    """Real key-by-key typing at a human pace, with an uneven rhythm."""
    for ch in text:
        cdp.send("Input.insertText", wait=False, text=ch)
        time.sleep(delay * rnd.uniform(0.6, 1.5) * PACE[0])
    nap(0.25)


def scroll_to(sel, text, offset=24):
    y = cdp.js(f"""(()=>{{const e=[...document.querySelectorAll({json.dumps(sel)})].find(e=>e.textContent.trim().startsWith({json.dumps(text)}));
      return e?e.getBoundingClientRect().top+window.scrollY-{offset}:null}})()""")
    if y is not None:
        smooth_scroll(y)
        nap(1.1)


def until(expr, timeout=240):
    t0 = now()
    while now() - t0 < timeout:
        if cdp.js(expr):
            return True
        time.sleep(0.25)
    print("   (timed out waiting for", expr[:60], ")", flush=True)
    return False


AITASK_DONE = "!document.getElementById('aitask')||!!(document.getElementById('ait-foot')||{}).textContent"


def ai_task(button_sel, button_text, label, timeout=240):
    click(button_sel, button_text)
    with fast("ai", label):
        drift()
        until(AITASK_DONE, timeout)
    time.sleep(2.9)                                               # the panel closes itself 2.6 s after a success


def sign_in(user, password="demo1234"):
    with fast("ui", "sign-in"):
        click("#lu")
        type_text(user, 0.06)
        click("#lp")
        type_text(password, 0.05)
        click("#lb")
        until("!document.getElementById('lu')", 30)
        nap(1.2)


def sign_out():
    click("button", "Sign out")
    until("!!document.getElementById('lu')", 20)
    nap(0.8)


def pick_address(address_typed, pick):
    """Type the address and pick the OpenStreetMap suggestion. Typed at normal speed (shown sped up): at slow-motion
    pace every key would start a new map search. The pick is checked ("On the map") and retried if needed."""
    with fast("ui", "address"):
        click("#na")
        type_text(address_typed, 0.06)
    for attempt in range(4):
        p = where(".sug-i", pick, 160)
        nap(0.3)
        p = where(".sug-i", pick, 40)                                 # measured again: the list may have just changed
        click_at(p["x"] + rnd.uniform(-40, 40), p["y"])
        if until("(document.getElementById('nloc')||{}).textContent.includes('On the map')", 12):
            return
        print("   address not picked, again", flush=True)
        with fast("ui", "address"):
            cdp.js("(()=>{const a=document.getElementById('na');a.value='';a.dispatchEvent(new Event('input',{bubbles:true}))})()")
            click("#na")
            type_text(address_typed, 0.06)
    raise RuntimeError("the address could not be picked")


def report(address_typed, pick, photo, text):
    """The 'Report a problem' page: address from the OpenStreetMap suggestions, a photo, one sentence."""
    click("aside nav a", "Report a problem")
    nap(1.0)
    pick_address(address_typed, pick)
    nap(0.6)
    p = where("#nf")
    move(p["x"], p["y"])
    root = cdp.send("DOM.getDocument", depth=-1)["root"]["nodeId"]
    node = cdp.send("DOM.querySelector", nodeId=root, selector="#nf")["nodeId"]
    cdp.send("DOM.setFileInputFiles", nodeId=node, files=[str(photo)])
    nap(0.7)
    click("#nd")
    type_text(text, 0.035)


# ---- browser
prof = OUT / "profile"
shutil.rmtree(prof, ignore_errors=True)
proc = subprocess.Popen([EDGE, "--headless=new", f"--force-device-scale-factor={SCALE}", "--lang=en-US", "--accept-lang=en-US", *os.environ.get("REC_FLAGS", "").split(), "--hide-scrollbars", "--remote-debugging-port=9340", f"--window-size={W},{H}",
                         f"--user-data-dir={prof}", "about:blank"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
merged = None
TEST = "--test" in sys.argv                                        # a short dry run of the mechanics only
try:
    for _ in range(60):
        try:
            tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9340/json"))
            break
        except Exception:
            time.sleep(0.3)
    cdp = CDP([t for t in tabs if t["type"] == "page"][0]["webSocketDebuggerUrl"])
    for m in ("Page.enable", "DOM.enable") + (() if os.environ.get("REC_NOANIM") else ("Animation.enable",)):
        cdp.send(m)
    cdp.send("Browser.setDownloadBehavior", behavior="allow", downloadPath=str((OUT / "downloads").resolve()))
    cdp.send("Emulation.setDeviceMetricsOverride", width=W, height=H, deviceScaleFactor=SCALE, mobile=False)
    # no red spell-check underlines in the video
    cdp.send("Page.addScriptToEvaluateOnNewDocument", source="document.addEventListener('focusin',e=>{if('spellcheck' in e.target)e.target.spellcheck=false},true)")
    cdp.send("Page.navigate", url=URL + "/")
    time.sleep(3)
    cdp.js("localStorage.clear()")
    cdp.send("Page.navigate", url=URL + "/")
    time.sleep(3)
    # the text caret blinks on the real clock: in slow motion played back fast it would strobe, so it is hidden
    css = "*{caret-color:transparent!important}" + os.environ.get("REC_CSS", "")
    cdp.js("(()=>{const s=document.createElement('style');s.textContent=" + json.dumps(css) + ";document.head.appendChild(s)})()")
    if not os.environ.get("REC_NOANIM"):
        cdp.send("Animation.setPlaybackRate", playbackRate=1 / SLOW)
    cdp.send("Page.startScreencast", format="jpeg", quality=90, maxWidth=int(W * SCALE), maxHeight=int(H * SCALE), everyNthFrame=1)
    time.sleep(0.5)
    _send_mouse(*CUR)
    cdp.recording = True
    T0 = now()

    if "--test-address" in sys.argv:
        caption("test")
        sign_in("citizen")
        click("aside nav a", "Report a problem")
        nap(1.0)
        pick_address("25 rue de siam brest", "25 Rue de Siam")
        print("nloc:", cdp.js("document.getElementById('nloc').textContent"), "| file button:", cdp.js("document.getElementById('nf').outerHTML.slice(0,80)"), flush=True)
        raise SystemExit
    if TEST:
        caption("test")
        sign_in("tech")
        click("aside nav a", "All tickets")
        nap(1.0)
        click("tbody tr", "IS-0042")
        nap(1.2)
        click(".tabs button", "AI report")
        nap(1.0)
        nap(1.0)
        print("doc height", cdp.js("(()=>{const d=document.createElement('div');d.style.height='2000px';document.querySelector('main').appendChild(d);return document.documentElement.scrollHeight})()"), flush=True)
        for lab in ("scroll down", "scroll up"):
            ta = now(); n0 = len(cdp.frames) + cdp.q.qsize()
            smooth_scroll(900 if lab == "scroll down" else 0, 1.6); time.sleep(1.6 * SLOW)
            print(f"{lab}: {(len(cdp.frames) + cdp.q.qsize() - n0) / (now() - ta):.1f} fps real", flush=True)
            nap(0.5)
        raise SystemExit

    # ---- intro
    caption("Live demo, recorded in one take: the real InfraSight app running on a laptop, calling Meta's models through the Meta Model API.")
    caption("Everything shown was built during the hackathon week (Oct 27 – Nov 4, 2026). When an AI call takes long, "
            "the video is sped up and says so in the top-right corner.")
    nap(5.0)

    # ---- 1. a citizen reports the smashed bus shelter
    caption("A citizen signs in. Every report must be placed on the map: they type an address and pick one of the OpenStreetMap suggestions.")
    sign_in("citizen")
    report("25 rue de siam brest", "25 Rue de Siam", PHOTO, "The bus shelter has been smashed: broken glass all over the pavement.")
    caption("They add one photo of the problem and one sentence in their own words. No form to fill in, no category to choose.", 4.0)
    nap(4.5)
    caption("When they send it, Muse Spark reads the photo and the sentence together: it names the problem, sets severity and "
            "urgency, finds who owns the street, and checks for duplicates nearby.", 4.5)
    nap(5.5)
    click("#nb")
    with fast("ai", "citizen report: Muse Spark, SAM 3.1, Muse Image"):
        drift()
        until("[...document.querySelectorAll('#pipe li')].length>0&&document.querySelectorAll('#pipe li')[0].className=='ok'")
        caption("Then SAM 3.1 outlines the damage on the photo, and Muse Image draws the street once repaired.")
        until("!!(document.getElementById('pipe-foot')||{}).textContent")
    hold(1.5)
    caption("The repair picture is always labelled as an illustration, never passed off as a photo.", 3.0)
    hold(3.5)
    click("#pipe-foot button", "Close")
    nap(0.8)
    sign_out()

    # ---- 2. a second citizen reports the same shelter: merged
    caption("A second citizen reports the same bus shelter a few metres away. Muse Spark compares it with the open cases "
            "nearby and merges it: one case, two citizens following it.")
    with fast("ui", "new account"):
        click("button", "Create an account")
        nap(0.8)
        click("#lu")
        type_text("lucia", 0.06)
        click("#ln")
        type_text("Lucia Garcia", 0.05)
        p = where("#ll")
        click_at(p["x"], p["y"])
        cdp.js("(()=>{const s=document.getElementById('ll');s.value='Spanish';s.dispatchEvent(new Event('change',{bubbles:true}))})()")
        nap(0.5)
        click("#lp")
        type_text("lucia-demo-2026", 0.04)
        click("#lb")
        until("!document.getElementById('lu')", 30)
        nap(1.0)
        report("25 rue de siam brest", "25 Rue de Siam", PHOTO2, "Bus stop destroyed, glass everywhere, people walk on it.")
    nap(0.8)
    click("#nb")
    with fast("ai", "second report: Muse Spark checks for duplicates"):
        drift()
        until("!!(document.getElementById('pipe-foot')||{}).textContent")
    merged = cdp.js("document.getElementById('pipe').textContent.includes('Same problem as')")
    print("   merged:", merged, flush=True)
    hold(5.0)
    click("#pipe-foot button", "Close")
    nap(0.8)

    # ---- 3. citizen updates, in the citizen's language
    caption("Each citizen picks the language of their updates, here Spanish. At every step of the repair, Muse Spark writes "
            "them a short update in that language.")
    click("aside nav a", "Updates")
    until("document.querySelectorAll('main .panel').length>0", 20)
    hold(5.0)
    sign_out()

    # ---- 4. the town hall: the map
    caption("The town hall's technician signs in. The map shows every open case by severity, the danger zones drawn by the AI, "
            "detours, and streets where problems keep coming back.")
    sign_in("tech")
    nap(1.2)
    click("#ai-zones")
    nap(1.0)
    click("#ai-zones")
    nap(1.0)
    click("#clear-all")
    nap(1.0)
    click("#clear-all")
    hold(1.5)

    # ---- 5. the merged ticket: before / after
    click("aside nav a", "All tickets")
    nap(1.0)
    click("tbody tr", "IS-0050")
    nap(1.2)
    caption("On the ticket, the before / after slider compares the citizen's photo with Muse Image's repair preview, "
            "next to the SAM 3.1 outline.")
    k = where(".cmp")
    y0 = k["y"] + rnd.uniform(-20, 20)
    pos = cdp.js("parseFloat(getComputedStyle(document.querySelector('.cmp')).getPropertyValue('--pos'))||50") or 50
    x_knob = k["l"] + k["w"] * pos / 100
    move(x_knob, y0)
    nap(0.15)
    cdp.send("Input.dispatchMouseEvent", type="mousePressed", x=x_knob, y=y0, button="left", buttons=1, clickCount=1)
    EVENTS["clicks"].append([now(), x_knob, y0])
    for frac, dur in ((0.08, 1.0), (0.92, 1.6), (0.35, 1.2)):        # drag the knob like a hand: left, all the way right, back
        _stroke(k["l"] + k["w"] * frac, y0 + rnd.uniform(-6, 6), dur, buttons=1, curve=False)
        nap(0.25)
    cdp.send("Input.dispatchMouseEvent", type="mouseReleased", x=CUR[0], y=CUR[1], button="left", buttons=0, clickCount=1)
    hold(2.0)

    # ---- 6. the pothole: damage analysis, full report, cost, stage draft
    click("aside nav a", "All tickets")
    nap(1.0)
    click("tbody tr", "IS-0042")
    nap(1.2)
    caption("'Outline and measure the damage' runs SAM 3.1 again, then Muse Spark estimates the real size from objects of "
            "known size, like the kerb or road markings.")
    nap(4.5)
    ai_task("button", "the damage", "damage analysis: SAM 3.1, Muse Spark, Muse Image")
    hold(2.5)
    smooth_scroll(0)
    nap(0.6)
    click(".tabs button", "AI report")
    nap(0.8)
    caption("'Generate full report': Muse Spark writes the decision report, with the responsible authority, the procurement "
            "route and the legal articles it relies on, or [verify] when unsure.")
    nap(5.0)
    ai_task("button", "Generate full report", "full report: Muse Spark")
    scroll_to("h2", "Regulatory path", 90)
    hold(2.5)
    caption("Costs are not invented: Muse Spark lists the work and the quantities, and the server prices each line from public "
            "price schedules, with a link to its source.", 4.0)
    scroll_to("h2", "Cost estimate", 24)
    hold(5.5)
    smooth_scroll(0)
    nap(0.6)
    click(".tabs button", "Pipeline")
    nap(1.0)
    caption("Every repair follows 7 legal stages. For the current stage, Muse Spark drafts the documents: here the decision memo, "
            "with budget impact and the rules that apply.")
    nap(5.0)
    ai_task("button", "AI assist for this stage", "stage draft: Muse Spark")
    y = cdp.js("(()=>{const a=[...document.querySelectorAll('.ao')].find(e=>e.textContent.trim().length>20);"
               "return a?a.getBoundingClientRect().top+window.scrollY-160:null})()")
    if y is not None:
        smooth_scroll(y)
    nap(0.8)
    hold(5.0)

    # ---- 7. a street closure: detour and traffic order
    click("aside nav a", "All tickets")
    nap(1.0)
    click("tbody tr", "IS-0044")
    nap(1.2)
    click(".tabs button", "Danger and zone")
    nap(2.0)
    caption("If the street must close, InfraSight downloads the road network from OpenStreetMap and computes the shortest "
            "legal detour around the closed section.")
    nap(4.5)
    ai_task("button", "Plan a detour", "detour: OpenStreetMap, Muse Spark")
    scroll_to("b", "Detour", 150)
    hold(2.5)
    caption("Muse Spark then drafts the mayor's temporary traffic order with that detour. What only the town hall can decide, "
            "like the dates and the order number, stays [to fill].", 4.0)
    scroll_to(".ao", "MUNICIPAL ORDER", 120)
    hold(5.5)

    # ---- 8. elected officials: dashboard, weekly brief, hotspots forecast
    click("aside nav a", "Dashboard")
    nap(1.2)
    caption("Elected officials get a dashboard of priorities, deadlines and budget, and a weekly brief written by Muse Spark "
            "from the week's figures.")
    nap(4.0)
    ai_task("button", "brief", "weekly brief: Muse Spark")
    hold(5.0)
    click("aside nav a", "Hotspots")
    nap(1.2)
    caption("Hotspots are streets where problems keep coming back. The demo data has none yet, so Muse Spark's forecast says "
            "the data is too thin, instead of inventing a risk.")
    nap(4.0)
    ai_task("button", "forecast", "forecast: Muse Spark")
    hold(4.5)

    # ---- 9. the PDF report, and the end
    click("aside nav a", "All tickets")
    nap(1.0)
    click("tbody tr", "IS-0042")
    nap(1.2)
    click(".tabs button", "AI report")
    nap(0.8)
    caption("Every case exports as a PDF incident report: images, sources, cost, the 7 stages, the detour and the traffic order. "
            "At acceptance, Muse Spark also checks the repair from the after photo.")
    click("button", "Download PDF report")
    hold(5.5)
    caption("Three Meta models working together in one real product: Muse Spark, SAM 3.1 and Muse Image. "
            "Code and setup: github.com/abdo0620/InfraSight")
    hold(6.0)
except SystemExit:
    pass
finally:
    cdp.recording = False
    T1 = now()
    try:
        cdp.send("Page.stopScreencast")
        cdp.q.join()
    except Exception:
        pass
    proc.terminate()
    time.sleep(1)
    shutil.rmtree(prof, ignore_errors=True)

json.dump({"t0": T0, "t1": T1, "frames": cdp.frames, "scale": SCALE}, open(OUT / "frames.json", "w"))
json.dump(EVENTS | {"merged": merged}, open(OUT / "events.json", "w"), indent=1)
print(f"recorded {len(cdp.frames)} frames over {T1 - T0:.1f} s ({len(cdp.frames) / (T1 - T0):.1f} fps average)")
