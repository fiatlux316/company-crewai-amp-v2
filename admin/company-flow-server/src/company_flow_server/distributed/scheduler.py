from __future__ import annotations
import os,time
from datetime import datetime,timezone
from croniter import croniter
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .db import init_db,SessionLocal,CrewSetting,ScheduleClaim,RunHistory
from .tasks import execute_crew
from company_flow_server.server.registry import CrewRegistry
import uuid

def main():
 init_db(); registry=CrewRegistry(os.getenv("CREW_REGISTRY_ROOT","team_registry"))
 interval=int(os.getenv("SCHEDULER_POLL_SECONDS","15"))
 while True:
  now=datetime.now(timezone.utc); minute=now.strftime("%Y%m%d%H%M")
  with SessionLocal() as db:
   rows=db.scalars(select(CrewSetting).where(CrewSetting.schedule_enabled.is_(True))).all()
   for cfg in rows:
    if not cfg.schedule_cron:continue
    # croniter.match allows multiple scheduler replicas; DB unique claim guarantees once/minute.
    if not croniter.match(cfg.schedule_cron,now):continue
    try:
     db.add(ScheduleClaim(crew_id=cfg.crew_id,minute_key=minute));db.commit()
    except IntegrityError:
     db.rollback();continue
    versions=registry.list_versions(cfg.crew_id)
    if not versions:continue
    rid=str(uuid.uuid4());inputs=cfg.default_inputs or {}
    db.add(RunHistory(run_id=rid,crew_id=cfg.crew_id,version=versions[-1],trigger="schedule",status="queued",inputs=inputs,verbose=["queued by distributed scheduler"]));db.commit()
    execute_crew.delay(rid,cfg.crew_id,versions[-1],inputs)
  time.sleep(interval)
if __name__=="__main__":main()
