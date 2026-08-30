from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field

class Severity(str, Enum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class IncidentState(str, Enum):
    detected = "detected"
    diagnosing = "diagnosing"
    awaiting_approval = "awaiting_approval"
    remediating = "remediating"
    verifying = "verifying"
    resolved = "resolved"
    escalated = "escalated"

class Risk(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    destructive = "destructive"

class TenantCreate(BaseModel):
    name: str
    plan: str = "pilot"
    autonomy_level: int = Field(default=1, ge=0, le=4)
    auto_purchase_limit_cad: float = Field(default=0, ge=0)

class DeviceCreate(BaseModel):
    tenant_id: UUID
    site_id: UUID | None = None
    hostname: str
    platform: str
    external_ids: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

class EventCreate(BaseModel):
    tenant_id: UUID
    device_id: UUID | None = None
    source: str
    event_type: str
    severity: Severity
    summary: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ActionRequest(BaseModel):
    action_type: str
    risk: Risk
    reversible: bool = True
    estimated_cost_cad: float = Field(default=0, ge=0)
    parameters: dict[str, Any] = Field(default_factory=dict)

class VerificationRequest(BaseModel):
    successful: bool
    evidence: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None

class PolicyDecision(BaseModel):
    allowed: bool
    requires_approval: bool
    reason: str
