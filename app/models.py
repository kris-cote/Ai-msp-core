from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid
from app.db import Base


def now_utc():
    return datetime.now(timezone.utc)


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200))
    plan: Mapped[str] = mapped_column(String(50), default="pilot")
    autonomy_level: Mapped[int] = mapped_column(Integer, default=1)
    auto_purchase_limit_cad: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Site(Base):
    __tablename__ = "sites"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[object] = mapped_column(Uuid, ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[object] = mapped_column(Uuid, ForeignKey("tenants.id"), index=True)
    site_id: Mapped[object | None] = mapped_column(Uuid, ForeignKey("sites.id"), nullable=True, index=True)
    hostname: Mapped[str] = mapped_column(String(255), index=True)
    platform: Mapped[str] = mapped_column(String(100))
    external_ids: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Event(Base):
    __tablename__ = "events"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[object] = mapped_column(Uuid, ForeignKey("tenants.id"), index=True)
    device_id: Mapped[object | None] = mapped_column(Uuid, ForeignKey("devices.id"), nullable=True, index=True)
    source: Mapped[str] = mapped_column(String(100), index=True)
    event_type: Mapped[str] = mapped_column(String(150), index=True)
    severity: Mapped[str] = mapped_column(String(30), index=True)
    summary: Mapped[str] = mapped_column(String(1000))
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Incident(Base):
    __tablename__ = "incidents"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[object] = mapped_column(Uuid, ForeignKey("tenants.id"), index=True)
    device_id: Mapped[object | None] = mapped_column(Uuid, ForeignKey("devices.id"), nullable=True, index=True)
    event_id: Mapped[object] = mapped_column(Uuid, ForeignKey("events.id"), index=True)
    state: Mapped[str] = mapped_column(String(50), default="detected", index=True)
    diagnosis: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    verification: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class Action(Base):
    __tablename__ = "actions"
    id: Mapped[object] = mapped_column(Uuid, primary_key=True, default=uuid4)
    incident_id: Mapped[object] = mapped_column(Uuid, ForeignKey("incidents.id"), index=True)
    action_type: Mapped[str] = mapped_column(String(150))
    risk: Mapped[str] = mapped_column(String(30))
    reversible: Mapped[bool] = mapped_column(Boolean, default=True)
    estimated_cost_cad: Mapped[float] = mapped_column(Float, default=0)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    policy_decision: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="proposed", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
