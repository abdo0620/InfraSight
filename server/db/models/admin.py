"""TIER 2 tables: department, SLA, fallback queue. A ticket with no rows here is still valid."""
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from db.models.core import new_id, utcnow


class Department(Base):
    __tablename__ = 'departments'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    categories: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # municipal categories accepted
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class SlaPolicy(Base):
    __tablename__ = 'sla_policies'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    category_pattern: Mapped[str | None] = mapped_column(String)   # 'a,b' or '*' or None
    severity_pattern: Mapped[str | None] = mapped_column(String)
    response_days: Mapped[float] = mapped_column(Float, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class TicketAdmin(Base):
    __tablename__ = 'ticket_admin'
    ticket_id: Mapped[str] = mapped_column(ForeignKey('tickets.id', ondelete='CASCADE'), primary_key=True)
    municipal_category: Mapped[str | None] = mapped_column(String)
    department_id: Mapped[str | None] = mapped_column(ForeignKey('departments.id'))
    sla_policy_id: Mapped[str | None] = mapped_column(ForeignKey('sla_policies.id'))
    sla_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assigned_by: Mapped[str | None] = mapped_column(String)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class UnclassifiedQueue(Base):
    """Catch-all worklist where tier 2/3 failures land."""
    __tablename__ = 'unclassified_municipal_queue'
    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    ticket_id: Mapped[str] = mapped_column(ForeignKey('tickets.id'), unique=True, nullable=False)
    reason: Mapped[str] = mapped_column(String, nullable=False)  # dept_mapping_failed|jurisdiction_lookup_failed
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
