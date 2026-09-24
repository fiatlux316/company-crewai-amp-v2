from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from company_flow_server.distributed.db import SessionLocal,CrewSetting,RunHistory
from company_flow_server.distributed.tasks import execute_crew
from .crew_admin import validate_cron

def iso(v): return v.isoformat() if v else None
def run_dict(r):
    meta = getattr(r, "metadata_json", {}) or {}
    artifacts = meta.get("artifacts", []) if isinstance(meta, dict) else []
    return {"run_id":r.run_id,"crew_id":r.crew_id,"version":r.version,"trigger":r.trigger,"status":r.status,"inputs":r.inputs or {},"outputs":r.outputs,"error":r.error,"verbose":r.verbose or [],"artifacts":artifacts,"created_at":iso(r.created_at),"started_at":iso(r.started_at),"ended_at":iso(r.ended_at)}
class CrewAdminServicePG:
 def __init__(self,registry,*args,**kwargs):self.registry=registry
 def start_scheduler(self):pass
 def stop_scheduler(self):pass
 def get_settings(self,cid):
  with SessionLocal() as db:
   x=db.get(CrewSetting,cid)
   return {"schedule":{"enabled":x.schedule_enabled,"cron":x.schedule_cron},"default_inputs":x.default_inputs or {},"metadata":x.metadata_json or {}} if x else {"schedule":{"enabled":False,"cron":""},"default_inputs":{},"metadata":{}}
 def patch_settings(self,cid,patch):
  with SessionLocal() as db:
   x=db.get(CrewSetting,cid) or CrewSetting(crew_id=cid);db.add(x)
   if "schedule" in patch:
    q=patch["schedule"]; cron=q.get("cron",x.schedule_cron)
    if cron:validate_cron(cron)
    x.schedule_cron=cron;x.schedule_enabled=q.get("enabled",x.schedule_enabled)
   if "default_inputs" in patch:x.default_inputs={**(x.default_inputs or {}),**patch["default_inputs"]}
   if "metadata" in patch:x.metadata_json={**(x.metadata_json or {}),**patch["metadata"]}
   db.commit()
  return self.get_settings(cid)
 def kickoff(self,cid,version,inputs=None,trigger="manual"):
  defaults=self.get_settings(cid)["default_inputs"]; merged={**defaults,**(inputs or {})};rid=str(uuid.uuid4())
  with SessionLocal() as db:
   r=RunHistory(run_id=rid,crew_id=cid,version=version,trigger=trigger,status="queued",inputs=merged,verbose=["queued to distributed worker"]);db.add(r);db.commit()
  execute_crew.delay(rid,cid,version,merged);return self.get_run(rid)
 def list_history(self,cid=None):
  with SessionLocal() as db:
   q=select(RunHistory)
   if cid:q=q.where(RunHistory.crew_id==cid)
   return [run_dict(x) for x in db.scalars(q.order_by(RunHistory.created_at.desc())).all()]
 def get_run(self,rid):
  with SessionLocal() as db:
   x=db.get(RunHistory,rid)
   if not x:raise KeyError(rid)
   return run_dict(x)
 def delete_run(self,rid):
  with SessionLocal() as db:
   x=db.get(RunHistory,rid)
   if not x:raise KeyError(rid)
   db.delete(x);db.commit()
