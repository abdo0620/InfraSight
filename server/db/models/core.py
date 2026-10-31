"""TIER 1 tables. Nothing here may depend on admin or compliance tables."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = 'users'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False, default='staff')  # staff | citizen
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Ticket(Base):
    """Core ticket. This table alone is enough for the app to work."""
    __tablename__ = 'tickets'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    public_ref: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default='submitted')
    category: Mapped[str] = mapped_column(String, nullable=False, default='uncategorized')
    severity: Mapped[str] = mapped_column(String, nullable=False, default='unknown')  # low|medium|high|unknown
    description: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float] = mapped_column(Float, nullable=False)   # PostGIS GEOGRAPHY in production
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    location_confidence: Mapped[float | None] = mapped_column(Float)
    photo_asset_id: Mapped[str | None] = mapped_column(String)
    needs_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    compliance_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1 | 2 | 3
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class TicketEvent(Base):
    """Append-only audit trail."""
    __tablename__ = 'ticket_events'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    ticket_id: Mapped[str] = mapped_column(ForeignKey('tickets.id'), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    actor: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Upload(Base):
    __tablename__ = 'uploads'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    ticket_id: Mapped[str | None] = mapped_column(ForeignKey('tickets.id'))
    kind: Mapped[str] = mapped_column(String, nullable=False)  # citizen_report|before|after|document
    storage_key: Mapped[str] = mapped_column(String, nullable=False)
    meta: Mapped[dict] = mapped_column('metadata', JSON, default=dict)  # sha256, size, quality flags
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TicketFallback(Base):
    """Every failed or skipped enrichment is recorded here, never swallowed."""
    __tablename__ = 'ticket_fallbacks'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    ticket_id: Mapped[str] = mapped_column(ForeignKey('tickets.id'), nullable=False, index=True)
    tier: Mapped[int] = mapped_column(Integer, nullable=False)  # 2 or 3
    step: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)  # provider_timeout|no_match|flag_disabled|...
    fallback: Mapped[str] = mapped_column(String, nullable=False)  # default_sla|unclassified_queue|skipped|...
    detail: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
