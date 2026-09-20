import json
from pathlib import Path
from company_flow_server.contracts.manifest import CrewManifest
from company_flow_server.server.flow_designer import recommend_connections, validate_schema_mappings
from company_flow_server.server.registry import CrewRegistry

def manifest(cid, inp, out, required=None):
    return CrewManifest.from_dict({"schema_version":1,"crew_id":cid,"version":"1","name":cid,"owner":"x","entrypoint":"x:run",
      "input_schema":{"type":"object","properties":inp,"required":required or []},"output_schema":{"type":"object","properties":out}})

def test_recommend_exact_name_and_type():
    a=manifest("a",{},{"analysis":{"type":"string"},"count":{"type":"integer"}})
    b=manifest("b",{"analysis":{"type":"string"}},{},["analysis"])
    r=recommend_connections(a,b)
    assert r[0]["source_field"]=="analysis" and r[0]["target_field"]=="analysis" and r[0]["score"]>=150

def test_recommend_integer_to_number():
    a=manifest("a",{},{"count":{"type":"integer"}})
    b=manifest("b",{"count":{"type":"number"}},{})
    r=recommend_connections(a,b)
    assert r[0]["source_field"]=="count"

def _write(root,cid,inp,out,required=None):
    d=root/cid/"1";d.mkdir(parents=True)
    (d/"crew-manifest.json").write_text(json.dumps({"schema_version":1,"crew_id":cid,"version":"1","name":cid,"owner":"x","entrypoint":"x:run",
      "input_schema":{"type":"object","properties":inp,"required":required or []},"output_schema":{"type":"object","properties":out}}))

def test_validate_type_mismatch(tmp_path):
    _write(tmp_path,"a",{},{"count":{"type":"string"}})
    _write(tmp_path,"b",{"count":{"type":"integer"}},{},["count"])
    reg=CrewRegistry(tmp_path)
    raw={"steps":[{"step_id":"a","crew_id":"a","version":"1","inputs":{}},{"step_id":"b","crew_id":"b","version":"1","inputs":{"count":"$steps.a.outputs.count"}}]}
    issues=validate_schema_mappings(raw,reg)
    assert any("type mismatch" in x["message"] for x in issues)
