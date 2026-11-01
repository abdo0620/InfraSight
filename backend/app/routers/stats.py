from collections import Counter
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..auth import staff
from ..db import Ticket, User, get_db

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats")
def stats(_u: User = Depends(staff), s: Session = Depends(get_db)):
    """Aggregates for the charts. The prototype computes the same numbers in the browser (frontend/js/app.js)."""
    rows = s.query(Ticket).all()
    weeks = Counter(min(5, (datetime.utcnow() - t.created).days // 7) for t in rows)
    cost: Counter = Counter()
    for t in rows:
        if t.cost_min is not None:
            cost[t.type] += (t.cost_min + t.cost_max) / 2
    return {"total": len(rows), "open": sum(t.st < 7 for t in rows),
            "by_severity": dict(Counter(t.sev for t in rows)), "by_type": dict(Counter(t.type for t in rows)),
            "by_stage": dict(Counter(t.st for t in rows)), "per_week": [weeks.get(5 - i, 0) for i in range(6)],
            "cost_by_type": dict(cost), "overdue": sum(t.due < 0 and t.st < 7 for t in rows)}
