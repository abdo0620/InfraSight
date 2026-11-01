import base64, html
from pathlib import Path
from ..schemas import ZONE_COLORS

e = html.escape


def _zone_text(z: dict) -> str:
    if z.get("shape") == "street":
        return f"street section {(z.get('street') or {}).get('name') or ''}, {z.get('radius_m', '?')} m affected".replace(" ,", ",")
    return f"{'area' if z.get('shape') == 'area' else 'point'}, radius {z.get('radius_m', '?')} m"


def _embed(path: str | None) -> str | None:
    return ("data:image/jpeg;base64," + base64.b64encode(Path(path).read_bytes()).decode()
            if path and Path(path).exists() else None)


def _figures(t: dict, paths: dict) -> str:
    """Photo, damage zone, repair preview and after-repair photo, side by side, with what each one is."""
    check = (t.get("after") or {}).get("check") or {}
    items = [("photo", "Citizen photo", "As reported."),
             ("zone", "Damage zone", "Damaged area in red" + (" (outlined by SAM 3.1)." if (t.get("damage") or {}).get("sam")
                                                              else " (located by the AI, approximate).")),
             ("preview", "Expected result after repair", "AI-generated illustration (Muse Image), not a photo."),
             ("after", "After repair", "Photo taken at acceptance."
              + (f" AI check: {check['verdict'].replace('_', ' ')}. {check.get('explanation', '')}" if check else ""))]
    cells = [f'<figure><img alt="{e(title)}" src="{src}"><figcaption><b>{e(title)}</b><br>{e(note)}</figcaption></figure>'
             for key, title, note in items if (src := _embed(paths.get(key)))]
    return f'<h2>Images</h2><div class="figs">{"".join(cells)}</div>' if cells else ""


def report_html(t: dict, paths: dict) -> str:
    """Self-contained report (front-end ticket shape). paths: photo, zone, preview, after (files in uploads/).
    The images are embedded, so they travel with the file."""
    r = t.get("rep") or {}
    img = _figures(t, paths)
    c, z = r.get("consequences") or t.get("cons") or {}, r.get("danger_zone") or t.get("zone") or {}
    lvl = z.get("level", t["sev"])
    li = lambda xs: "<ul>" + "".join(f"<li>{e(str(x))}</li>" for x in xs or []) + "</ul>"
    events = "".join(f"<li>{e(x['event'])} ({e(x['likelihood'])}): {e(x['impact'])}</li>" for x in c.get("potential_events", []))
    acts = "".join(f"<tr><td>{e(a['step'])}</td><td>{e(a['owner'])}</td><td>{e(a['deadline'])}</td></tr>" for a in r.get("actions", []))
    logs = "".join(f"<tr><td>{e(l['d'])}</td><td>{e(l['w'])}</td><td>{e(l['e'])}</td></tr>" for l in t["log"])
    a = r.get("authority", {})
    return f"""<!doctype html><meta charset="utf-8"><title>{e(t['ref'])}</title>
<style>body{{font:14px sans-serif;max-width:820px;margin:20px auto}}td,th{{border-bottom:1px solid #ddd;padding:4px;text-align:left}}
.figs{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:12px}}figure{{margin:0}}
figure img{{width:100%;border-radius:4px;border:1px solid #ddd}}figcaption{{font-size:12px;color:#444;margin-top:4px}}</style>
<h1>{e(t['ref'])} - {e(t['title'])}</h1><p>{e(t['addr'])} ({t.get('lat')}, {t.get('lng')})</p>{img}
<p><b>Severity:</b> {r.get('severity', t['sev'])} {e(r.get('severity_reason', ''))}</p>
<p style="border-left:6px solid {ZONE_COLORS.get(lvl, '#888')};padding-left:8px"><b>Danger zone:</b> level {lvl}, {e(_zone_text(z))}. {e(z.get('description', ''))}</p>
<h2>Consequences</h2><p>{e(c.get('danger_type', 'not assessed'))}{' (access blocked)' if c.get('blocked_access') else ''}</p><ul>{events}</ul>{li(c.get('immediate_measures'))}
<h2>Who to contact</h2><p><b>{e(a.get('primary', ''))}</b> {e(a.get('contact_reason', ''))}</p>
<h2>Actions</h2><table>{acts}</table><h2>Audit log</h2><table>{logs}</table><p><i>AI-generated. Human review required.</i></p>"""
