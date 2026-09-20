from pathlib import Path
import json
import zipfile

from company_flow_server.server.registry import CrewRegistry


def test_registry_deploy(tmp_path: Path):
    project = tmp_path / "project"
    (project / "src" / "demo").mkdir(parents=True)
    manifest = {
        "schema_version": 1,
        "crew_id": "demo.crew",
        "version": "1.0.0",
        "name": "Demo",
        "owner": "tester",
        "entrypoint": "demo.entrypoint:run",
        "input_schema": {"type": "object", "required": [], "properties": {}},
        "output_schema": {"type": "object", "required": [], "properties": {}},
    }
    (project / "crew-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (project / "src" / "demo" / "entrypoint.py").write_text("def run(inputs, runtime): return {}\n", encoding="utf-8")
    artifact = tmp_path / "demo.crew-1.0.0.crewpkg"
    with zipfile.ZipFile(artifact, "w") as zf:
        zf.write(project / "crew-manifest.json", "crew-manifest.json")
        zf.write(project / "src" / "demo" / "entrypoint.py", "src/demo/entrypoint.py")
    registry = CrewRegistry(tmp_path / "registry")
    deployed = registry.deploy(artifact)
    assert deployed.crew_id == "demo.crew"
    assert registry.resolve("demo.crew", "1.0.0").is_dir()
