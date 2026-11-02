import re, threading
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from .config import settings
from .db import Base, add_missing_columns, engine
from .regulations import public_meta
from .routers import auth, insights, stats, tickets
from .seed import fill_geo, seed

Base.metadata.create_all(engine)       # creates infrasight.db on first start. TODO: Alembic migrations
add_missing_columns()
seed()
threading.Thread(target=fill_geo, daemon=True).start()
app = FastAPI(title="InfraSight API")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_methods=["*"], allow_headers=["*"])
for r in (auth.router, tickets.router, stats.router, insights.router):
    app.include_router(r)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/meta")
def meta():
    """Stages, checklists, directory and update languages for the console (public, no AI prompts)."""
    return public_meta() | {"langs": auth.LANGS}


FRONTEND = Path(__file__).resolve().parents[2] / "frontend"


@app.get("/", include_in_schema=False)
@app.get("/index.html", include_in_schema=False)
def index():
    """index.html with a version on each local script and stylesheet (js/app.js?v=...). The version changes with any
    frontend file, so a browser can never mix a new page with scripts it cached from an older version."""
    version = str(int(max(p.stat().st_mtime for p in FRONTEND.rglob("*") if p.is_file())))
    html = re.sub(r'((?:src|href)="(?:js|css)/[^"?]+)"', rf'\1?v={version}"', (FRONTEND / "index.html").read_text("utf-8"))
    return HTMLResponse(html, headers={"Cache-Control": "no-cache"})


class Console(StaticFiles):
    """The frontend files, re-checked by the browser on every load (cheap: unchanged files answer 304). Without it a
    browser can keep an old app.js next to a new index.html after an update."""

    async def get_response(self, path, scope):
        r = await super().get_response(path, scope)
        r.headers["Cache-Control"] = "no-cache"
        return r


# The console itself, so one server (http://localhost:8000) runs everything. Mounted last: /api/* wins.
app.mount("/", Console(directory=FRONTEND, html=True), name="frontend")
