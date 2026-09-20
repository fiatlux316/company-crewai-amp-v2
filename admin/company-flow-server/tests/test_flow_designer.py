from pathlib import Path
import json

from company_flow_server.server.flow_designer import validate_flow_payload
from company_flow_server.server.registry import CrewRegistry


def _deploy_dir(root: Path, crew_id: str, version: str, input_props=None, output_props=None):
    d=root/crew_id/version
    d.mkdir(parents=True)
    (d/"crew-manifest.json").write_text(json.dumps({
        "schema_version":1,"crew_id":crew_id,"version":version,"name":crew_id,
        "owner":"tester","entrypoint":"x:run",
        "input_schema":{"type":"object","properties":input_props or {}},
        "output_schema":{"type":"object","properties":output_props or {}}
    }))


def test_designer_validates_previous_step_reference(tmp_path):
    _deploy_dir(tmp_path,"a","1.0.0",output_props={"analysis":{"type":"string"}})
    _deploy_dir(tmp_path,"b","1.0.0",input_props={"analysis":{"type":"string"}})
    registry=CrewRegistry(tmp_path)
    raw={"flow_id":"f","version":"1","name":"F","steps":[
        {"step_id":"one","crew_id":"a","version":"1.0.0","inputs":{}},
        {"step_id":"two","crew_id":"b","version":"1.0.0","inputs":{"analysis":"$steps.one.outputs.analysis"}}
    ],"output":{}}
    assert validate_flow_payload(raw,registry)==[]


def test_designer_rejects_future_reference(tmp_path):
    _deploy_dir(tmp_path,"a","1.0.0")
    registry=CrewRegistry(tmp_path)
    raw={"flow_id":"f","version":"1","name":"F","steps":[
        {"step_id":"one","crew_id":"a","version":"1.0.0","inputs":{"x":"$steps.two.outputs.x"}},
        {"step_id":"two","crew_id":"a","version":"1.0.0","inputs":{}}
    ],"output":{}}
    assert any("previous step" in x for x in validate_flow_payload(raw,registry))
