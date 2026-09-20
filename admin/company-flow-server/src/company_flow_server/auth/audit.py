from company_flow_server.distributed.db import SessionLocal,AuditLog
def audit(actor,action,resource,outcome="success",detail=None):
 with SessionLocal() as db:
  db.add(AuditLog(actor=actor,action=action,resource=resource,outcome=outcome,detail=detail or {}));db.commit()
