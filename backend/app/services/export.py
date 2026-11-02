"""Incident report as an A4 PDF (ReportLab), downloaded from the ticket's AI report tab.

Accessibility: real selectable text (no scanned pages), document language and title (shown by the viewer),
a bookmark per section, high-contrast colours, and a caption under every image. ReportLab cannot write a fully
tagged PDF (PDF/UA), so screen readers get the text in reading order but not the structure tags or image alt text."""
import io
from datetime import date, timedelta
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Flowable, Frame, Image, KeepTogether, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)
from ..regulations import OWNERS, STAGES
from ..schemas import ZONE_COLORS

# ---- look: same palette as the console (frontend/css/styles.css)
INK, MUTED, LINE, PANEL = colors.HexColor("#1c1917"), colors.HexColor("#5f5853"), colors.HexColor("#e5dfd8"), colors.HexColor("#faf7f3")
ACCENT, ACCENT_SOFT = colors.HexColor("#c2603f"), colors.HexColor("#fbeee8")
GREEN, AMBER, RED = colors.HexColor("#15803d"), colors.HexColor("#b45309"), colors.HexColor("#b91c1c")
LOGO = (colors.HexColor("#f0a07c"), colors.HexColor("#d97757"), colors.HexColor("#a8452a"))
W, H = A4
MARGIN = 18 * mm

_fonts = Path(__import__("reportlab").__file__).parent / "fonts"      # Bitstream Vera, shipped with ReportLab
if "Sans" not in pdfmetrics.getRegisteredFontNames():
    for name, file in (("Sans", "Vera.ttf"), ("Sans-Bold", "VeraBd.ttf"), ("Sans-Italic", "VeraIt.ttf"),
                       ("Sans-BoldItalic", "VeraBI.ttf")):
        pdfmetrics.registerFont(TTFont(name, str(_fonts / file)))
    pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans-Italic", boldItalic="Sans-BoldItalic")

S = {
    "body": ParagraphStyle("body", fontName="Sans", fontSize=9.2, leading=13, textColor=INK, alignment=TA_LEFT),
    "muted": ParagraphStyle("muted", fontName="Sans", fontSize=8.2, leading=11.5, textColor=MUTED),
    "small": ParagraphStyle("small", fontName="Sans", fontSize=7.6, leading=10.2, textColor=MUTED),
    "cell": ParagraphStyle("cell", fontName="Sans", fontSize=8.4, leading=11.4, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="Sans-Bold", fontSize=8.4, leading=11.4, textColor=INK),
    "label": ParagraphStyle("label", fontName="Sans-Bold", fontSize=7, leading=9, textColor=MUTED),
    "h1": ParagraphStyle("h1", fontName="Sans-Bold", fontSize=12.5, leading=16, textColor=INK, spaceBefore=12,
                         spaceAfter=6, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName="Sans-Bold", fontSize=9.6, leading=13, textColor=INK, spaceBefore=6,
                         spaceAfter=3, keepWithNext=1),
    "title": ParagraphStyle("title", fontName="Sans-Bold", fontSize=19, leading=23, textColor=INK),
    "quote": ParagraphStyle("quote", fontName="Sans-Italic", fontSize=9.2, leading=13.5, textColor=INK, leftIndent=8),
}


def e(x) -> str:
    return escape(str(x if x is not None else ""))


def P(text: str, style: str = "body") -> Paragraph:
    return Paragraph(text, S[style])


# ---------------------------------------------------------------------------------------------------------------
# Logo (vector copy of the console logo: gradient rounded square + serif wordmark)
# ---------------------------------------------------------------------------------------------------------------

def draw_logo(c, x: float, y: float, size: float = 14, word: bool = True, word_size: float = 15) -> None:
    c.saveState()
    p = c.beginPath()
    p.roundRect(x, y, size, size, size * 0.33)
    c.clipPath(p, stroke=0, fill=0)
    c.linearGradient(x, y + size, x + size, y, LOGO, positions=(0, 0.6, 1), extend=False)
    c.restoreState()
    if word:
        c.setFont("Times-Bold", word_size)
        c.setFillColor(INK)
        c.drawString(x + size + 6, y + size * 0.16, "InfraSight")


# ---------------------------------------------------------------------------------------------------------------
# Small building blocks
# ---------------------------------------------------------------------------------------------------------------

class Chip(Flowable):
    """Rounded label: severity, stage, owner..."""

    def __init__(self, text: str, fill, ink=colors.white, size: float = 7.8):
        super().__init__()
        self.text, self.fill, self.ink, self.size = text, fill, ink, size
        self.width = pdfmetrics.stringWidth(text, "Sans-Bold", size) + 12
        self.height = size + 7

    def draw(self):
        self.canv.setFillColor(self.fill)
        self.canv.roundRect(0, 0, self.width, self.height, self.height / 2, stroke=0, fill=1)
        self.canv.setFillColor(self.ink)
        self.canv.setFont("Sans-Bold", self.size)
        self.canv.drawString(6, 3.6, self.text)


def chips(items: list) -> Table:
    t = Table([items], hAlign="LEFT")
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                           ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return t


def sev_color(n) -> colors.Color:
    return colors.HexColor(ZONE_COLORS.get(max(1, min(5, int(n or 3))), "#888888"))


def box(rows: list, widths: list, header: bool = False, zebra: bool = True) -> Table:
    """Table with light rules; rows are lists of Paragraphs or strings."""
    data = [[c if isinstance(c, Flowable) else P(e(c), "cell") for c in r] for r in rows]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    st = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE),
          ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
          ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), PANEL), ("LINEBELOW", (0, 0), (-1, 0), 0.8, MUTED)]
    if zebra:
        st += [("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, colors.HexColor("#fcfbf9")])]
    t.setStyle(TableStyle(st))
    return t


def facts(pairs: list, label_w: float = 34 * mm) -> Table:
    """Two-column key/value list."""
    return box([[P(e(k).upper(), "label"), v if isinstance(v, Flowable) else P(e(v), "cell")] for k, v in pairs if v
                not in (None, "", [])], [label_w, W - 2 * MARGIN - label_w], zebra=False)


def bullets(items: list, style: str = "body") -> list:
    return [Paragraph(e(x), S[style], bulletText="•") for x in items if x]


def note(text: str, fill=ACCENT_SOFT, ink=INK) -> Table:
    t = Table([[P(text, "muted")]], colWidths=[W - 2 * MARGIN], hAlign="LEFT")
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fill), ("LEFTPADDING", (0, 0), (-1, -1), 8),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("LINEBEFORE", (0, 0), (0, -1), 2.2, ACCENT)]))
    return t


class H1(Paragraph):
    """Section heading that also becomes a PDF bookmark."""

    def __init__(self, text: str):
        super().__init__(e(text), S["h1"])
        self.bookmark = text


def figure(path: str | None, caption: str, detail: str, width: float):
    if not path or not Path(path).exists():
        return None
    iw, ih = ImageReader(path).getSize()
    h = width * ih / iw
    img = Image(path, width=width, height=h)
    cap = P(f"<b>{e(caption)}</b><br/>{detail}", "small")
    t = Table([[img], [cap]], colWidths=[width])
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("TOPPADDING", (0, 1), (-1, 1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                           ("BOX", (0, 0), (0, 0), 0.4, LINE)]))
    return t


# ---------------------------------------------------------------------------------------------------------------
# Page furniture: header on page 1, slim header after, footer with "page x of y" everywhere
# ---------------------------------------------------------------------------------------------------------------

class NumberedCanvas(rl_canvas.Canvas):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._pages = []

    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._pages)
        for state in self._pages:
            self.__dict__.update(state)
            self._footer(total)
            super().showPage()
        super().save()

    def _footer(self, total: int):
        self.setStrokeColor(LINE)
        self.setLineWidth(0.5)
        self.line(MARGIN, 13 * mm, W - MARGIN, 13 * mm)
        self.setFont("Sans", 7)
        self.setFillColor(MUTED)
        self.drawString(MARGIN, 9 * mm, f"InfraSight · Incident report {self._ref} · generated {date.today():%d %b %Y}")
        self.drawRightString(W - MARGIN, 9 * mm, f"Page {self._pageNumber} of {total}")
        self.drawCentredString(W / 2, 5.5 * mm, "Content marked as AI-generated is a draft: a technician or elected "
                                                "official decides.")


class ReportDoc(BaseDocTemplate):
    def __init__(self, buf, ref: str, title: str):
        super().__init__(buf, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN, topMargin=30 * mm,
                         bottomMargin=19 * mm, title=f"Incident report {ref}: {title}", author="InfraSight",
                         subject="Public space incident report", creator="InfraSight", lang="en-GB",
                         displayDocTitle=True)
        self.ref = ref
        first = Frame(MARGIN, 19 * mm, W - 2 * MARGIN, H - 19 * mm - 20 * mm, id="first")
        rest = Frame(MARGIN, 19 * mm, W - 2 * MARGIN, H - 19 * mm - 22 * mm, id="rest")
        self.addPageTemplates([PageTemplate("first", [first], onPage=self._first, autoNextPageTemplate="rest"),
                               PageTemplate("rest", [rest], onPage=self._rest)])

    def _first(self, c, doc):
        c._ref = self.ref
        draw_logo(c, MARGIN, H - 15 * mm, size=15, word_size=17)
        c.setFont("Sans-Bold", 7.5)
        c.setFillColor(ACCENT)
        c.drawRightString(W - MARGIN, H - 11 * mm, "INCIDENT REPORT")
        c.setFont("Sans", 8)
        c.setFillColor(MUTED)
        c.drawRightString(W - MARGIN, H - 15 * mm, f"{self.ref} · {date.today():%d %B %Y}")
        c.setStrokeColor(LINE)
        c.line(MARGIN, H - 18 * mm, W - MARGIN, H - 18 * mm)

    def _rest(self, c, doc):
        c._ref = self.ref
        draw_logo(c, MARGIN, H - 13 * mm, size=10, word_size=11.5)
        c.setFont("Sans", 7.5)
        c.setFillColor(MUTED)
        c.drawRightString(W - MARGIN, H - 11.5 * mm, f"Incident report {self.ref}")
        c.setStrokeColor(LINE)
        c.line(MARGIN, H - 16 * mm, W - MARGIN, H - 16 * mm)

    def afterFlowable(self, f):
        if isinstance(f, H1):
            key = f"s{id(f)}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(f.bookmark, key, level=0)


# ---------------------------------------------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------------------------------------------

URGENCY = {5: "make safe today", 4: "within 48 hours", 3: "within 1 week", 2: "within 2 weeks", 1: "planned"}
VERDICT = {"repaired": ("Repaired", GREEN), "partial": ("Partly repaired", AMBER),
           "not_repaired": ("Not repaired", RED), "unclear": ("Unclear", MUTED)}


def _zone_text(z: dict) -> str:
    shape = z.get("shape") or "point"
    if shape == "street":
        name = (z.get("street") or {}).get("name")
        return f"Street section{(' ' + name) if name else ''}, about {z.get('radius_m', '?')} m affected"
    return f"{'Area' if shape == 'area' else 'Localised point'}, radius about {z.get('radius_m', '?')} m"


def report_pdf(t: dict, paths: dict) -> bytes:
    """t: the ticket as the console sees it (serializers.to_front). paths: photo, zone, preview, after (uploads/)."""
    r = t.get("rep") or {}
    c = r.get("consequences") or t.get("cons") or {}
    z = r.get("danger_zone") or t.get("zone") or {}
    dmg, after, detour = t.get("damage") or {}, t.get("after") or {}, t.get("detour") or {}
    st = t.get("st", 0)
    stage = STAGES[st]["n"] if st < len(STAGES) else "Closed"
    reported = date.today() - timedelta(days=t.get("age") or 0)
    full = W - 2 * MARGIN
    story: list = []

    # ---- title block
    story += [P(e(t["title"]), "title"), Spacer(1, 3),
              P(f"{e(t['ref'])} · {e(t['addr'])} · reported {reported:%d %B %Y}", "muted"), Spacer(1, 8)]
    story.append(chips([Chip(f"Severity {t['sev']}/5", sev_color(t["sev"])),
                        Chip(f"Urgency {t['urg']}/5", sev_color(t["urg"])),
                        Chip("Closed" if st >= len(STAGES) else f"Stage {st + 1}/7 · {stage}", INK),
                        Chip(OWNERS.get(t.get("owner"), t.get("owner") or "Owner not set"), PANEL, ink=INK)]))
    if t.get("merged_into"):
        story += [Spacer(1, 6), note(f"This report was merged into <b>{e(t['merged_into'])}</b>, which handles the same "
                                     "problem.")]

    # ---- at a glance
    story.append(H1("At a glance"))
    cost = t.get("cost")
    due = t.get("due")
    story.append(facts([
        ("Reference", t["ref"]), ("Type", t["type"]), ("Address", t["addr"]),
        ("Coordinates", f"{t['lat']:.5f}, {t['lng']:.5f}" if t.get("lat") is not None else "Not pinned on the map"),
        ("Reported", f"{reported:%d %B %Y}" + (f" · {t['followers']} other citizen(s) reported it too"
                                               if t.get("followers") else "")),
        ("Responsible", OWNERS.get(t.get("owner"), "")),
        ("Current stage", "Closed" if st >= len(STAGES) else f"{st + 1} of 7 · {stage}"),
        ("Next deadline", None if due is None else (f"{-due} day(s) overdue" if due < 0 else "today" if due == 0
                                                   else f"in {due} day(s)")),
        ("Estimated cost", f"EUR {cost[0]:,.0f} to {cost[1]:,.0f} excl. VAT" if cost else "To estimate"),
    ]))

    # ---- description
    story += [H1("Citizen's description"), P(e(t.get("desc")), "quote")]

    # ---- images, two per row
    col = (full - 6 * mm) / 2
    sam = dmg.get("sam")
    check = after.get("check") or {}
    figs = [figure(paths.get("photo"), "Photo", "As reported by the citizen.", col),
            figure(paths.get("zone"), "Damage zone",
                   "Damaged area in red, " + ("outlined by SAM 3.1." if sam else "located by the AI (approximate)."), col),
            figure(paths.get("preview"), "Expected result after repair",
                   "AI-generated illustration (Muse Image), <b>not a photo</b>.", col),
            figure(paths.get("after"), "After repair",
                   "Photo taken at acceptance." + (f" AI check: {VERDICT.get(check.get('verdict'), ('?',))[0]}."
                                                   if check else ""), col)]
    figs = [f for f in figs if f]
    if figs:
        story.append(H1("Images"))
        for i in range(0, len(figs), 2):           # one table per row, so a row can start under the heading
            row = figs[i:i + 2] + ([""] if len(figs[i:i + 2]) == 1 else [])
            g = Table([row], colWidths=[col + 6 * mm, col], hAlign="LEFT")
            g.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                   ("RIGHTPADDING", (0, 0), (0, -1), 6 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
            story.append(g)

    # ---- damage measurement
    size = dmg.get("size")
    if size:
        story.append(KeepTogether([H1("Damage measurement"), facts([
            ("Size", f"about {size.get('width_m')} m × {size.get('length_m')} m, {size.get('area_m2')} m²"
                     + (f", {size['depth_cm']} cm deep" if size.get("depth_cm") else "")),
            ("Confidence", (size.get("confidence") or "").capitalize()),
            ("Based on", size.get("basis")),
        ]), Spacer(1, 3), P("Estimated by Muse Spark from objects of known size in the photo. Measure on site before "
                            "ordering.", "small")]))

    # ---- danger
    story.append(H1("Danger and consequences"))
    lvl = int(z.get("level") or t["sev"])
    story.append(facts([
        ("Main danger", c.get("danger_type") or "Not assessed yet"),
        ("Access", "Blocked for vehicles or pedestrians" if c.get("blocked_access") else "Not blocked"),
        ("Danger zone", Paragraph(f'<font color="{ZONE_COLORS.get(lvl, "#888888")}"><b>Level {lvl}/5</b></font> · '
                                  f'{e(_zone_text(z))}' + (f". {e(z.get('description'))}" if z.get("description") else ""),
                                  S["cell"]) if z else None),
        ("People at risk", c.get("vulnerable_people")),
    ]))
    events = c.get("potential_events") or []
    if events:
        story += [Spacer(1, 6), P("If nothing is done", "h2"),
                  box([[P("<b>Possible event</b>", "cell"), P("<b>Likelihood</b>", "cell"), P("<b>Impact</b>", "cell")]]
                      + [[x.get("event"), (x.get("likelihood") or "").capitalize(), x.get("impact")] for x in events],
                      [full * 0.45, full * 0.15, full * 0.40], header=True)]
    if c.get("immediate_measures"):
        story += [Spacer(1, 4), P("Immediate measures", "h2")] + bullets(c["immediate_measures"])

    # ---- AI assessment
    story.append(H1("AI assessment"))
    if not r:
        story.append(note("No full AI report yet. Use “Generate full report” on the ticket's AI report tab."))
    else:
        a, g, k = r.get("authority") or {}, r.get("regulatory") or {}, r.get("cost") or {}
        story += [note("Drafted by <b>Muse Spark</b> from the photo, the ticket and the regulatory notes. Legal points "
                       "cite their source or are marked [verify]. A technician or elected official decides."),
                  Spacer(1, 6), P("Classification", "h2"),
                  facts([("Type", r.get("type")),
                         ("Severity", Paragraph(f"<b>{e(r.get('severity'))}/5</b> · {e(r.get('severity_reason'))}",
                                                S["cell"])),
                         ("Urgency", f"{(r.get('urgency') or '').capitalize()}" + (f" · first response: "
                                                                                   f"{r.get('response_time')}" if
                                                                                   r.get("response_time") else "")),
                         ("Ownership", r.get("ownership_assessment"))]),
                  Spacer(1, 4), P("Who to contact", "h2"),
                  facts([("Responsible", Paragraph(f"<b>{e(a.get('primary'))}</b>", S["cell"])),
                         ("Also inform", "; ".join(x for x in a.get("secondary") or [] if x)),
                         ("Why", a.get("contact_reason"))]),
                  Spacer(1, 4), P("Regulatory path", "h2"),
                  facts([("Procurement", g.get("procurement")),
                         ("Council vote", "Required" if g.get("council_vote") else "Not required")])]
        if g.get("authorizations"):
            story += [P("Authorizations before works", "muted")] + bullets(g["authorizations"], "cell")
        if g.get("legal_notes"):
            story += [Spacer(1, 3), P("Legal notes", "muted")] + bullets(g["legal_notes"], "cell")
        story += [Spacer(1, 4), P("Cost estimate", "h2"),
                  facts([("Range", f"EUR {k.get('min', 0):,.0f} to {k.get('max', 0):,.0f} excl. VAT"),
                         ("Basis", k.get("basis"))])]
        if r.get("risks"):
            story += [Spacer(1, 4), P("Risks", "h2")] + bullets(r["risks"])
        if r.get("actions"):
            story += [Spacer(1, 4), P("Recommended actions", "h2"),
                      box([[P("<b>#</b>", "cell"), P("<b>Step</b>", "cell"), P("<b>Owner</b>", "cell"),
                            P("<b>Deadline</b>", "cell")]]
                          + [[str(i + 1), x.get("step"), x.get("owner"), x.get("deadline")]
                             for i, x in enumerate(r["actions"])],
                          [8 * mm, full * 0.52, full * 0.22, full - 8 * mm - full * 0.74], header=True)]
        if r.get("citizen_message"):
            story += [Spacer(1, 4), P("Message to the citizen", "h2"), P(e(r["citizen_message"]), "quote")]

    # ---- progress
    story.append(CondPageBreak(60 * mm))
    story.append(H1("Progress through the 7 stages"))
    ch = t.get("ch") or {}
    rows = [[P("<b>#</b>", "cell"), P("<b>Stage</b>", "cell"), P("<b>Status</b>", "cell"), P("<b>Checklist</b>", "cell")]]
    for i, s in enumerate(STAGES):
        done = sum(1 for k in range(len(s["c"])) if ch.get(f"{i}:{k}"))
        status = ("Done", GREEN) if i < st else ("Current", ACCENT) if i == st else ("Upcoming", MUTED)
        rows.append([str(i + 1), s["n"], Paragraph(f'<font color="#{status[1].hexval()[2:]}"><b>'
                                                   f'{status[0]}</b></font>', S["cell"]), f"{done} of {len(s['c'])}"])
    story.append(box(rows, [8 * mm, full * 0.55, full * 0.18, full - 8 * mm - full * 0.73], header=True))

    # ---- repair check
    if after:
        v = VERDICT.get(check.get("verdict"), ("Not checked by the AI", MUTED))
        story.append(KeepTogether([H1("Repair check"), facts([
            ("Verdict", Paragraph(f'<font color="#{v[1].hexval()[2:]}"><b>{e(v[0])}</b></font>', S["cell"])),
            ("Explanation", check.get("explanation")),
            ("Still to fix", "; ".join(x for x in check.get("remaining_issues") or [] if x) or "Nothing reported"),
        ]), Spacer(1, 3), P("Muse Spark compared the red-marked photo with the after-repair photo. Confirm on site.",
                            "small")]))

    # ---- detour
    if detour:
        story.append(KeepTogether([H1("Detour"), facts([
            ("Length", f"{detour.get('length_m')} m"),
            ("Via", " > ".join(detour.get("streets") or []) or "local roads"),
        ]), Spacer(1, 3), P("Computed from the OpenStreetMap road network, one-way streets respected. The draft traffic "
                            "order is in the annex." if detour.get("order") else "Computed from OpenStreetMap.",
                            "small")]))

    # ---- history
    story.append(H1("History"))
    log = t.get("log") or []
    story.append(box([[P("<b>Date</b>", "cell"), P("<b>By</b>", "cell"), P("<b>Event</b>", "cell")]]
                     + [[x.get("d"), x.get("w"), x.get("e")] for x in log] if log else [["No events"]],
                     [22 * mm, 36 * mm, full - 58 * mm] if log else [full], header=bool(log)))

    # ---- annex: traffic order
    if detour.get("order"):
        story.append(H1("Annex: draft traffic order"))
        story.append(note("Drafted in French by Muse Spark for the mayor to check, complete and sign. "
                          "[à compléter] = value to fill; [à vérifier] = point to check."))
        story.append(Spacer(1, 6))
        story += [P(e(line) or "&nbsp;", "cell") for line in detour["order"].splitlines()]

    buf = io.BytesIO()
    ReportDoc(buf, t["ref"], t["title"]).build(story, canvasmaker=NumberedCanvas)
    return buf.getvalue()
