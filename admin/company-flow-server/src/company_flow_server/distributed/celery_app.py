from __future__ import annotations
import os
from celery import Celery
celery_app=Celery("company_flow_server",broker=os.getenv("CELERY_BROKER_URL","redis://localhost:6379/0"),backend=os.getenv("CELERY_RESULT_BACKEND","redis://localhost:6379/1"))
celery_app.conf.update(task_track_started=True,worker_prefetch_multiplier=1,task_acks_late=True,task_reject_on_worker_lost=True,result_expires=86400,timezone="UTC")
celery_app.autodiscover_tasks(["company_flow_server.distributed"])
