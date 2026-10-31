from datetime import datetime, timezone

from pydantic import BaseModel


def iso(dt: datetime | None) -> str | None:
    """SQLite returns naive datetimes: they are stored as UTC."""
    if dt is None:
        return None
    return (dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)).isoformat()


class LoginIn(BaseModel):
    username: str
    password: str


class TicketPatch(BaseModel):
    category: str | None = None
    department_id: str | None = None
    status: str | None = None
