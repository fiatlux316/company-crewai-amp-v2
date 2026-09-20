import json
from pathlib import Path
from company_flow_server.server.crew_admin import CrewAdminService, cron_matches
from company_flow_server.server.registry import CrewRegistry
from datetime import datetime

class DummyExecutor: pass

def test_schedule_survives_independent_registry_change(tmp_path):
    reg=CrewRegistry(tmp_path/'registry'); svc=CrewAdminService(reg,DummyExecutor(),tmp_path/'state')
    svc.patch_settings('ops.a',{'schedule':{'enabled':True,'cron':'*/5 * * * *'},'default_inputs':{'x':1}})
    # Administrator state is independent of deployment/package lifecycle.
    assert svc.get_settings('ops.a')['schedule']['cron']=='*/5 * * * *'
    assert svc.get_settings('ops.a')['default_inputs']['x']==1

def test_cron_match():
    assert cron_matches('*/5 * * * *', datetime(2026,1,1,10,15))
    assert not cron_matches('*/5 * * * *', datetime(2026,1,1,10,16))
