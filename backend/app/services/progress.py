"""Live progress of an AI action, so the console can show each real step while the request runs.

The console sends a random id in the X-Progress header with the action, and reads GET /api/progress/{id} every
0.4 s. Each endpoint marks its steps: run, then ok or err, with a short detail ("Severity 4/5 · Roads department").
Kept in memory for 10 minutes (one server process)."""
import re, threading, time
from contextlib import contextmanager
from fastapi import Header

_jobs: dict[str, dict] = {}
_lock = threading.Lock()
TTL = 600


class Progress:
    def __init__(self, job: str | None):
        self.job = job

    def set(self, key: str, state: str, detail: str | None = None) -> None:
        if not self.job:
            return
        now = time.time()
        with _lock:
            j = _jobs.setdefault(self.job, {"t": now, "steps": {}})
            j["steps"][key] = {"state": state, "detail": detail}
            for k in [k for k, v in _jobs.items() if now - v["t"] > TTL]:
                del _jobs[k]

    @contextmanager
    def step(self, key: str):
        """with p.step("spark") as st: ...; st["detail"] = "..."  -> run, then ok (or err if it raises)."""
        self.set(key, "run")
        st = {"detail": None}
        try:
            yield st
        except Exception as e:
            self.set(key, "err", getattr(e, "detail", None) or str(e) or "Failed")
            raise
        self.set(key, "ok", st["detail"])


def progress_of(x_progress: str | None = Header(None)) -> Progress:
    """FastAPI dependency: the action's progress tracker (no-op without a valid X-Progress header)."""
    return Progress(x_progress if x_progress and re.fullmatch(r"[A-Za-z0-9-]{8,64}", x_progress) else None)


def get(job: str) -> dict:
    with _lock:
        j = _jobs.get(job)
        return {"steps": {k: dict(v) for k, v in j["steps"].items()}} if j else {"steps": {}}
