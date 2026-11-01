import threading
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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


# The console itself, so one server (http://localhost:8000) runs everything. Mounted last: /api/* wins.
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parents[2] / "frontend", html=True), name="frontend")
