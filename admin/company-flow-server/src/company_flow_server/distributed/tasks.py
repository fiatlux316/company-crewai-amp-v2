from __future__ import annotations
from datetime import datetime, timezone
from .celery_app import celery_app
from .db import SessionLocal, RunHistory
from company_flow_server.server.registry import CrewRegistry
from company_flow_server.server.executor import CrewExecutor
import os

def now(): return datetime.now(timezone.utc)

@celery_app.task(name="crew.execute",bind=True,autoretry_for=(),max_retries=0)
def execute_crew(self,run_id:str,crew_id:str,version:str,inputs:dict):
    with SessionLocal() as db:
        rec=db.get(RunHistory,run_id)
        if not rec:return
        rec.status="running";rec.started_at=now();rec.verbose=list(rec.verbose or [])+["distributed worker started"];db.commit()
    try:
        registry=CrewRegistry(os.getenv("CREW_REGISTRY_ROOT","team_registry"))
        result=CrewExecutor(registry).run(crew_id,version,inputs,correlation_id=run_id)
        with SessionLocal() as db:
            rec=db.get(RunHistory,run_id);rec.status="succeeded";rec.ended_at=now();rec.outputs=result.outputs
            rec.verbose=list(rec.verbose or [])+list(result.metadata.get("verbose",[]) if isinstance(result.metadata,dict) else [])
            db.commit()
    except Exception as exc:
        with SessionLocal() as db:
            rec=db.get(RunHistory,run_id)
            if rec:rec.status="failed";rec.ended_at=now();rec.error=str(exc);rec.verbose=list(rec.verbose or [])+[f"ERROR: {exc}"];db.commit()
        raise
