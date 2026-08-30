from uuid import UUID, uuid4
from fastapi import FastAPI, HTTPException
from app.schemas import TenantCreate, DeviceCreate, EventCreate, ActionRequest, VerificationRequest, IncidentState
from app.policy import evaluate_action

app = FastAPI(title="AI MSP 2.0 Core", version="0.1.0", description="Autonomous multi-tenant IT operations core")

# MVP in-memory stores. PostgreSQL repository layer replaces these next.
tenants = {}
devices = {}
incidents = {}
actions = {}

@app.get("/health")
def health():
    return {"status":"ok","service":"ai-msp-core","version":"0.1.0"}

@app.get("/v1/system/capabilities")
def capabilities():
    return {
        "lifecycle":["detect","normalize","enrich","diagnose","assess_risk","check_policy","protect","remediate","verify","document","learn","close_or_escalate"],
        "domains":["hardware","software","patching","backup","security","network","identity","cloud","user_reported"],
        "autonomy_levels": {"0":"observe","1":"recommend","2":"safe_auto","3":"managed_auto","4":"advanced_auto"}
    }

@app.post("/v1/tenants")
def create_tenant(body: TenantCreate):
    tenant_id = uuid4()
    record = {"id":tenant_id, **body.model_dump(), "auto_purchase_limit_cad":0.0}
    tenants[tenant_id] = record
    return record

@app.post("/v1/devices")
def create_device(body: DeviceCreate):
    if body.tenant_id not in tenants:
        raise HTTPException(404,"Tenant not found")
    device_id = uuid4()
    record = {"id":device_id, **body.model_dump()}
    devices[device_id] = record
    return record

@app.post("/v1/events")
def ingest_event(body: EventCreate):
    if body.tenant_id not in tenants:
        raise HTTPException(404,"Tenant not found")
    incident_id = uuid4()
    incident = {
        "id":incident_id,
        "tenant_id":body.tenant_id,
        "device_id":body.device_id,
        "state":IncidentState.detected,
        "event":body.model_dump(),
        "diagnosis":None,
        "verification":None
    }
    incidents[incident_id] = incident
    return incident

@app.get("/v1/incidents")
def list_incidents(tenant_id: UUID | None = None):
    values = list(incidents.values())
    return [i for i in values if tenant_id is None or i["tenant_id"] == tenant_id]

@app.post("/v1/incidents/{incident_id}/evaluate")
def evaluate_incident(incident_id: UUID):
    incident = incidents.get(incident_id)
    if not incident:
        raise HTTPException(404,"Incident not found")
    incident["state"] = IncidentState.diagnosing
    # Next milestone: telemetry enrichment + LLM diagnosis/tool planning.
    return {"incident_id":incident_id,"state":incident["state"],"next":"collect_telemetry_and_diagnose"}

@app.post("/v1/incidents/{incident_id}/actions")
def propose_action(incident_id: UUID, body: ActionRequest):
    incident = incidents.get(incident_id)
    if not incident:
        raise HTTPException(404,"Incident not found")
    tenant = tenants[incident["tenant_id"]]
    decision = evaluate_action(body, tenant["autonomy_level"], tenant["auto_purchase_limit_cad"])
    action_id = uuid4()
    record = {"id":action_id,"incident_id":incident_id,"request":body.model_dump(),"policy":decision.model_dump(),"status":"approved_for_execution" if decision.allowed else "awaiting_approval"}
    actions[action_id] = record
    incident["state"] = IncidentState.remediating if decision.allowed else IncidentState.awaiting_approval
    return record

@app.post("/v1/incidents/{incident_id}/verify")
def verify_incident(incident_id: UUID, body: VerificationRequest):
    incident = incidents.get(incident_id)
    if not incident:
        raise HTTPException(404,"Incident not found")
    incident["verification"] = body.model_dump()
    incident["state"] = IncidentState.resolved if body.successful else IncidentState.escalated
    return incident
