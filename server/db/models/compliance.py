"""TIER 3 tables: jurisdiction, permits, utility alerts, SOP documents. Entirely droppable."""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from db.models.core import new_id, utcnow


class Jurisdiction(Base):
    __tablename__ = 'jurisdictions'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)  # e.g. 'fr-paris'
    name: Mapped[str] = mapped_column(String, nullable=False)
    region: Mapped[str | None] = mapped_column(String)
    country: Mapped[str] = mapped_column(String, nullable=False, default='FR')
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # bbox, utility_alert, rule versions
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class TicketCompliance(Base):
    __tablename__ = 'ticket_compliance'
    ticket_id: Mapped[str] = mapped_column(ForeignKey('tickets.id', ondelete='CASCADE'), primary_key=True)
    jurisdiction_id: Mapped[str | None] = mapped_column(ForeignKey('jurisdictions.id'))
    jurisdiction_confidence: Mapped[float | None] = mapped_column(Float)
    zoning_result: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, nullable=False, default='pending')
    # pending | in_progress | complete | degraded | skipped
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class TicketPermitCheck(Base):
    __tablename__ = 'ticket_permit_checks'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    ticket_id: Mapped[str] = mapped_column(ForeignKey('tickets.id'), nullable=False, index=True)
    permit_type: Mapped[str] = mapped_column(String, nullable=False)
    requirement: Mapped[str] = mapped_column(String, nullable=False)
    checklist: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String, nullable=False, default='not_started')
    # not_started | waived | in_progress | satisfied | failed
    source_rule: Mapped[str | None] = mapped_column(String)  # rule id + version
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TicketUtilityAlert(Base):
    __tablename__ = 'ticket_utility_alerts'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    ticket_id: Mapped[str] = mapped_column(ForeignKey('tickets.id'), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    alert_ref: Mapped[str | None] = mapped_column(String)
    operators: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String, nullable=False, default='pending')
    # pending | sent | responses_received | failed
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class TicketSopDocument(Base):
    __tablename__ = 'ticket_sop_documents'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    ticket_id: Mapped[str] = mapped_column(ForeignKey('tickets.id'), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)  # public_works_sop | traffic_management_plan
    content: Mapped[dict] = mapped_column(JSON, nullable=False)
    ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    human_approved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    approved_by: Mapped[str | None] = mapped_column(String)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
