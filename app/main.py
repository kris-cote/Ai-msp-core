from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import Base, engine, get_db
from app.models import Tenant, Device, Event, Incident, Action
from app.policy import evaluate_action
from app.queue import enqueue_incident
from app.schemas import TenantCreate, DeviceCreate, EventCreate, ActionRequest, VerificationRequest, IncidentState

app = FastAPI(title="AI MSP 2.0 Core", version="0.2.0", description="Autonomous multi-tenant IT operations core")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
def health():
    return {"status":"ok","service":"ai-msp-core","version":"0.2.0"}

@app.get("/v1/system/capabilities")
def capabilities():
    return {
        "lifecycle":["detect","normalize","enrich","diagnose","assess_risk","check_policy","protect","remediate","verify","document","learn","close_or_escalate"],
        "domains":["hardware","software","patching","backup","security","network","identity","cloud","user_reported"],
        "autonomy_levels":{"0":"observe","1":"recommend","2":"safe_auto","3":"managed_auto","4":"advanced_auto"}
    }

@app.post("/v1/tenants")
def create_tenant(body: TenantCreate, db: Session = Depends(get_db)):
    row = Tenant(name=body.name, plan=body.plan, autonomy_level=body.autonomy_level, auto_purchase_limit_cad=body.auto_purchase_limit_cad)
    db.add(row); db.commit(); db.refresh(row)
    return {"id":row.id,"name":row.name,"plan":row.plan,"autonomy_level":row.autonomy_level,"auto_purchase_limit_cad":row.auto_purchase_limit_cad}

@app.post("/v1/devices")
def create_device(body: DeviceCreate, db: Session = Depends(get_db)):
    if not db.get(Tenant, body.tenant_id):
        raise HTTPException(404,"Tenant not found")
    row = Device(tenant_id=body.tenant_id, site_id=body.site_id, hostname=body.hostname, platform=body.platform, external_ids=body.external_ids, metadata_json=body.metadata)
    db.add(row); db.commit(); db.refresh(row)
    return {"id":row.id,"tenant_id":row.tenant_id,"hostname":row.hostname,"platform":row.platform}

@app.post("/v1/events")
def ingest_event(body: EventCreate, db: Session = Depends(get_db)):
    if not db.get(Tenant, body.tenant_id):
        raise HTTPException(404,"Tenant not found")
    event = Event(tenant_id=body.tenant_id, device_id=body.device_id, source=body.source, event_type=body.event_type, severity=body.severity.value, summary=body.summary, evidence=body.evidence, occurred_at=body.occurred_at)
    db.add(event); db.flush()
    incident = Incident(tenant_id=body.tenant_id, device_id=body.device_id, event_id=event.id, state=IncidentState.detected.value)
    db.add(incident); db.commit(); db.refresh(incident)
    queued = enqueue_incident(str(incident.id))
    return {"id":incident.id,"tenant_id":incident.tenant_id,"device_id":incident.device_id,"event_id":incident.event_id,"state":incident.state,"queued":queued}

@app.get("/v1/incidents")
def list_incidents(tenant_id: UUID | None = None, db: Session = Depends(get_db)):
    q = db.query(Incident)
    if tenant_id:
        q = q.filter(Incident.tenant_id == tenant_id)
    rows = q.order_by(Incident.created_at.desc()).limit(200).all()
    return [{"id":r.id,"tenant_id":r.tenant_id,"device_id":r.device_id,"event_id":r.event_id,"state":r.state,"diagnosis":r.diagnosis,"verification":r.verification} for r in rows]

@app.post("/v1/incidents/{incident_id}/evaluate")
def evaluate_incident(incident_id: UUID, db: Session = Depends(get_db)):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404,"Incident not found")
    incident.state = IncidentState.diagnosing.value
    db.commit()
    return {"incident_id":incident_id,"state":incident.state,"next":"collect_telemetry_and_diagnose"}

@app.post("/v1/incidents/{incident_id}/actions")
def propose_action(incident_id: UUID, body: ActionRequest, db: Session = Depends(get_db)):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404,"Incident not found")
    tenant = db.get(Tenant, incident.tenant_id)
    decision = evaluate_action(body, tenant.autonomy_level, tenant.auto_purchase_limit_cad)
    action = Action(incident_id=incident.id, action_type=body.action_type, risk=body.risk.value, reversible=body.reversible, estimated_cost_cad=body.estimated_cost_cad, parameters=body.parameters, policy_decision=decision.model_dump(), status="approved_for_execution" if decision.allowed else "awaiting_approval")
    db.add(action)
    incident.state = IncidentState.remediating.value if decision.allowed else IncidentState.awaiting_approval.value
    db.commit(); db.refresh(action)
    return {"id":action.id,"incident_id":incident.id,"status":action.status,"policy":action.policy_decision}

@app.post("/v1/incidents/{incident_id}/verify")
def verify_incident(incident_id: UUID, body: VerificationRequest, db: Session = Depends(get_db)):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404,"Incident not found")
    incident.verification = body.model_dump()
    incident.state = IncidentState.resolved.value if body.successful else IncidentState.escalated.value
    db.commit()
    return {"id":incident.id,"state":incident.state,"verification":incident.verification}
