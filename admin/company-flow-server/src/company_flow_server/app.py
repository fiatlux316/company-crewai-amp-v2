from __future__ import annotations

import os
from pathlib import Path
import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .server.executor import CrewExecutor
from .server.flow_registry import FlowRegistry
from .server.orchestrator import FlowOrchestrator
from .server.registry import CrewRegistry
from .server.crew_admin_pg import CrewAdminServicePG
from .distributed.db import init_db, SessionLocal, AuditLog
from .auth.rbac import Principal, current_principal, require, require_owner_or
from .auth.audit import audit
from .mcp.registry import get_mcp_catalog
from .runtime.llm_gateway import router as llm_gateway_router
from .server.crew_graph import build_crew_graph
from .server.flow_designer import (
    validate_flow_payload, build_flow_graph, recommend_connections, validate_schema_mappings
)


REGISTRY_ROOT = os.getenv("CREW_REGISTRY_ROOT", "team_registry")
FLOW_ROOT = os.getenv("FLOW_ROOT", "flows")
DEPLOY_TOKEN = os.getenv("CREW_DEPLOY_TOKEN")

registry = CrewRegistry(REGISTRY_ROOT)
executor = CrewExecutor(registry)
admin_service = CrewAdminServicePG(registry)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Company Crew Flow Server", version="0.4.0", lifespan=lifespan, docs_url="/docs", redoc_url="/redoc")
flow_registry = FlowRegistry(FLOW_ROOT)
orchestrator = FlowOrchestrator(executor)
app.include_router(llm_gateway_router)


class CrewKickoffRequest(BaseModel):
    inputs: dict = Field(default_factory=dict)

class CrewSettingsRequest(BaseModel):
    schedule: dict | None = None
    default_inputs: dict | None = None
    metadata: dict | None = None

class FlowRunRequest(BaseModel):
    inputs: dict = Field(default_factory=dict)
    approved: bool = False
    change_ticket: str | None = None
    tool_runtime: dict[str, dict] = Field(default_factory=dict)


def _check_deploy_token(authorization: str | None) -> None:
    if not DEPLOY_TOKEN:
        return
    expected = f"Bearer {DEPLOY_TOKEN}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="invalid deploy token")






@app.get("/api/v1/crew")
@app.get("/api/v1/crews")
def list_crews(p: Principal = Depends(require("crew:read"))) -> dict:
    rows = registry.list_deployments()
    for row in rows:
        cfg = admin_service.get_settings(row["crew_id"])
        row["admin"] = cfg
        row.update(cfg.get("metadata", {}))
    return {"crews": rows}




@app.get("/api/v1/crews/{crew_id}/{version}/detail")
def crew_detail(crew_id: str, version: str, p: Principal = Depends(require("crew:read"))) -> dict:
    try:
        manifest = registry.manifest(crew_id, version)
        base = next(x for x in registry.list_deployments() if x["crew_id"]==crew_id and x["version"]==version)
    except (KeyError, StopIteration) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    cfg=admin_service.get_settings(crew_id)
    base["admin"]=cfg; base.update(cfg.get("metadata", {}))
    return base

@app.patch("/api/v1/crews/{crew_id}/settings")
def update_crew_settings(crew_id: str, request: CrewSettingsRequest, p: Principal = Depends(current_principal)) -> dict:
    versions=registry.list_versions(crew_id)
    if not versions: raise HTTPException(404,"crew not found")
    owner=registry.manifest(crew_id,versions[-1]).owner
    require_owner_or("crew:settings",crew_id,owner,p)
    patch={k:v for k,v in request.model_dump().items() if v is not None}
    try:
        result=admin_service.patch_settings(crew_id, patch); audit(p.subject,"crew.settings",crew_id,detail=patch); return result
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.delete("/api/v1/crews/{crew_id}/{version}")
def delete_crew(crew_id: str, version: str, confirm: bool=False, p: Principal = Depends(require("crew:delete"))) -> dict:
    if not confirm: raise HTTPException(status_code=400, detail="confirmation required")
    try: registry.delete(crew_id, version)
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    audit(p.subject,"crew.delete",f"{crew_id}@{version}")
    return {"status":"deleted","crew_id":crew_id,"version":version}

@app.post("/api/v1/crews/{crew_id}/{version}/kickoff", status_code=202)
def kickoff_crew(crew_id: str, version: str, request: CrewKickoffRequest, p: Principal = Depends(current_principal)) -> dict:
    try: registry.resolve(crew_id, version)
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    perm = "crew:kickoff:prod" if os.getenv("COMPANY_ENV","dev") == "prod" else "crew:kickoff:dev"
    if not p.allowed(perm): raise HTTPException(status_code=403, detail=f"permission required: {perm}")
    result=admin_service.kickoff(crew_id, version, request.inputs)
    audit(p.subject,"crew.kickoff",f"{crew_id}@{version}",detail={"run_id":result["run_id"]})
    return result

@app.get("/api/v1/crews/{crew_id}/runs")
def crew_runs(crew_id: str, p: Principal = Depends(require("run:read"))) -> dict:
    return {"runs": admin_service.list_history(crew_id)}

@app.get("/api/v1/runs")
def all_runs(p: Principal = Depends(require("run:read"))) -> dict:
    return {"runs": admin_service.list_history()}

@app.get("/api/v1/runs/{run_id}")
def run_detail(run_id: str, p: Principal = Depends(require("run:read"))) -> dict:
    try: return admin_service.get_run(run_id)
    except KeyError as exc: raise HTTPException(status_code=404, detail="run not found") from exc

@app.delete("/api/v1/runs/{run_id}")
def delete_run(run_id: str, confirm: bool=False, p: Principal = Depends(require("run:delete"))) -> dict:
    if not confirm: raise HTTPException(status_code=400, detail="confirmation required")
    try: admin_service.delete_run(run_id)
    except KeyError as exc: raise HTTPException(status_code=404, detail="run not found") from exc
    audit(p.subject,"run.delete",run_id)
    return {"status":"deleted","run_id":run_id}

@app.get("/api/v1/mcp/tools")
def mcp_tools(p: Principal = Depends(require("mcp:read"))) -> dict:
    return {"tools": get_mcp_catalog()}


@app.get("/api/v1/crews/{crew_id}/{version}/graph")
def crew_graph(crew_id: str, version: str) -> dict:
    try:
        return build_crew_graph(registry.resolve(crew_id, version))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc




class FlowSaveRequest(BaseModel):
    flow_id: str
    version: str = "1.0.0"
    name: str
    description: str = ""
    steps: list[dict]
    output: dict = Field(default_factory=dict)


@app.get("/api/v1/flows")
def list_flows(p: Principal = Depends(require("flow:read"))) -> dict:
    return {"flows": flow_registry.list()}


@app.get("/api/v1/flows/{flow_id}")
def get_flow(flow_id: str) -> dict:
    try:
        flow = flow_registry.load(flow_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return build_flow_graph(flow, registry)


@app.post("/api/v1/flows/validate")
def validate_flow(request: FlowSaveRequest) -> dict:
    raw = request.model_dump()
    errors = validate_flow_payload(raw, registry)
    schema_issues = validate_schema_mappings(raw, registry) if not errors else []
    schema_errors = [x["message"] for x in schema_issues if x["level"] == "error"]
    return {"valid": not errors and not schema_errors, "errors": errors, "schema_issues": schema_issues}


@app.put("/api/v1/flows/{flow_id}")
def save_flow(flow_id: str, request: FlowSaveRequest, p: Principal = Depends(require("flow:write"))) -> dict:
    raw = request.model_dump()
    if flow_id != raw["flow_id"]:
        raise HTTPException(status_code=400, detail="path flow_id and body flow_id must match")
    errors = validate_flow_payload(raw, registry)
    schema_issues = validate_schema_mappings(raw, registry) if not errors else []
    schema_errors = [x for x in schema_issues if x["level"] == "error"]
    if errors or schema_errors:
        raise HTTPException(status_code=400, detail={"errors": errors, "schema_issues": schema_issues})
    flow_registry.save(raw); audit(p.subject,"flow.save",flow_id,detail={"version":raw["version"]})
    return {"status": "saved", "flow_id": flow_id, "version": raw["version"]}




@app.get("/api/v1/schema/recommend")
def recommend_schema_mapping(source_crew_id: str, source_version: str, target_crew_id: str, target_version: str) -> dict:
    try:
        source = registry.manifest(source_crew_id, source_version)
        target = registry.manifest(target_crew_id, target_version)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "source": f"{source_crew_id}@{source_version}",
        "target": f"{target_crew_id}@{target_version}",
        "recommendations": recommend_connections(source, target),
    }



@app.get("/api/v1/auth/me")
def auth_me(p: Principal = Depends(current_principal)):
    return {"subject":p.subject,"roles":p.roles,"scopes":p.scopes,"environment":p.environment}

@app.get("/api/v1/audit")
def audit_logs(limit:int=100,p:Principal=Depends(require("audit:read"))):
    with SessionLocal() as db:
        rows=db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit,500)).all()
        return {"items":[{"id":x.id,"actor":x.actor,"action":x.action,"resource":x.resource,"outcome":x.outcome,"detail":x.detail,"created_at":x.created_at.isoformat()} for x in rows]}

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/v1/crews/{crew_id}/versions")
def list_versions(crew_id: str) -> dict:
    return {"crew_id": crew_id, "versions": registry.list_versions(crew_id)}


@app.post("/api/v1/crews/deploy")
async def deploy_crew(
    request: Request,
    x_crew_filename: str | None = Header(default=None),
    p: Principal = Depends(require("crew:deploy")),
) -> dict:
    if not x_crew_filename or not x_crew_filename.endswith(".crewpkg"):
        raise HTTPException(status_code=400, detail="X-Crew-Filename must be a .crewpkg name")
    payload = await request.body()
    if not payload:
        raise HTTPException(status_code=400, detail="empty package")
    with tempfile.TemporaryDirectory() as tmp:
        artifact = Path(tmp) / Path(x_crew_filename).name
        artifact.write_bytes(payload)
        try:
            manifest = registry.deploy(artifact)
        except FileExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (ValueError, KeyError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    audit(p.subject,"crew.deploy",f"{manifest.crew_id}@{manifest.version}")
    return {"status": "deployed", "crew_id": manifest.crew_id, "version": manifest.version}


@app.post("/api/v1/flows/{flow_id}/run")
def run_flow(flow_id: str, request: FlowRunRequest) -> dict:
    try:
        flow = flow_registry.load(flow_id)
        result = orchestrator.run(
            flow,
            request.inputs,
            approved=request.approved,
            change_ticket=request.change_ticket,
            tool_runtime=request.tool_runtime,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "flow_id": result.flow_id,
        "correlation_id": result.correlation_id,
        "outputs": result.outputs,
        "steps": result.steps,
    }


# Mount React SPA
import os
frontend_dist = Path(os.getenv("FRONTEND_DIST_DIR", "/app/frontend_dist"))
if not frontend_dist.exists():
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"

app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="spa")
