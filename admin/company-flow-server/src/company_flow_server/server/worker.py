from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import sys
import traceback
import uuid

# Safe storage path patch to prevent appdirs / crewai PermissionError in server/container
try:
    import appdirs
    def _safe_user_data_dir(appname=None, appauthor=None, version=None, roaming=False):
        base = Path(os.getenv("CREWAI_STORAGE_DIR") or Path.cwd() / ".crewai_storage")
        if appname:
            base = base / appname
        try:
            base.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return str(base)
    appdirs.user_data_dir = _safe_user_data_dir
except Exception:
    pass

from company_flow_server.bootstrap import build_llm_registry, build_policy_engine, build_tool_registry
from company_flow_server.config.settings import Settings
from company_flow_server.contracts.manifest import CrewManifest
from company_flow_server.runtime.server_runtime import ServerCrewRuntime
from company_flow_server.contracts.validation import validate_contract
from company_flow_server.policy.models import ToolExecutionContext


import shutil

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployed-dir", required=True)
    args = parser.parse_args()
    deployed = Path(args.deployed_dir).resolve()
    os.chdir(deployed)

    try:
        request = json.loads(sys.stdin.read())
        manifest = CrewManifest.load(deployed / "crew-manifest.json")
        inputs = request["inputs"]
        validate_contract(inputs, manifest.input_schema, label="inputs")

        sys.path.insert(0, str(deployed / "src"))
        module_name, callable_name = manifest.entrypoint.split(":", 1)
        entrypoint = getattr(importlib.import_module(module_name), callable_name)

        run_id = request.get("correlation_id") or str(uuid.uuid4())
        settings = Settings.from_env()
        runtime = ServerCrewRuntime(
            settings=settings,
            llms=build_llm_registry(settings),
            tools=build_tool_registry(settings),
            policy_engine=build_policy_engine(),
            execution_context=ToolExecutionContext(
                environment=settings.environment,
                correlation_id=run_id,
                approved=bool(request.get("approved", False)),
                change_ticket=request.get("change_ticket"),
            ),
            tool_runtime=request.get("tool_runtime", {}),
        )

        (deployed / "output").mkdir(parents=True, exist_ok=True)

        result = entrypoint(inputs, runtime)
        if not isinstance(result, dict):
            raise TypeError("crew entrypoint must return a dict")
        outputs = result.get("outputs", result)
        metadata = dict(result.get("metadata", {})) if "outputs" in result else {}
        if not isinstance(outputs, dict) or not isinstance(metadata, dict):
            raise TypeError("crew result must be {'outputs': dict, 'metadata': dict} or a plain output dict")
        validate_contract(outputs, manifest.output_schema, label="outputs")

        # Collect generated artifact files
        artifacts_root = Path(os.getenv("ARTIFACTS_ROOT", "artifacts")).resolve()
        artifacts_dir = artifacts_root / run_id
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        artifacts_list = []
        candidate_paths = set()
        output_dir = deployed / "output"
        if output_dir.exists():
            for p in output_dir.rglob("*"):
                if p.is_file():
                    candidate_paths.add(p)
        for p in deployed.glob("*"):
            if p.is_file() and p.name not in {"crew-manifest.json", "package.crewpkg", "deployment.json", "pyproject.toml", "tasks.jsonc", "agents.jsonc"}:
                if p.suffix in {".md", ".json", ".csv", ".pdf", ".txt", ".png", ".html", ".yaml", ".yml"}:
                    candidate_paths.add(p)

        for src_path in candidate_paths:
            try:
                rel_path = src_path.relative_to(deployed)
            except ValueError:
                rel_path = Path(src_path.name)
            dest_file = artifacts_dir / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest_file)
            artifacts_list.append({
                "filename": str(rel_path),
                "size": src_path.stat().st_size
            })

        metadata["artifacts"] = artifacts_list

        print(json.dumps({"ok": True, "outputs": outputs, "metadata": metadata}, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "error_type": type(exc).__name__, "traceback": traceback.format_exc()}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()

