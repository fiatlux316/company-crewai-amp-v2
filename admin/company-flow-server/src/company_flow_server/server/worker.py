from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys
import traceback
import uuid

from company_flow_server.bootstrap import build_llm_registry, build_policy_engine, build_tool_registry
from company_flow_server.config.settings import Settings
from company_flow_server.contracts.manifest import CrewManifest
from company_flow_server.runtime.server_runtime import ServerCrewRuntime
from company_flow_server.contracts.validation import validate_contract
from company_flow_server.policy.models import ToolExecutionContext


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployed-dir", required=True)
    args = parser.parse_args()
    deployed = Path(args.deployed_dir).resolve()

    try:
        request = json.loads(sys.stdin.read())
        manifest = CrewManifest.load(deployed / "crew-manifest.json")
        inputs = request["inputs"]
        validate_contract(inputs, manifest.input_schema, label="inputs")

        sys.path.insert(0, str(deployed / "src"))
        module_name, callable_name = manifest.entrypoint.split(":", 1)
        entrypoint = getattr(importlib.import_module(module_name), callable_name)

        settings = Settings.from_env()
        runtime = ServerCrewRuntime(
            settings=settings,
            llms=build_llm_registry(settings),
            tools=build_tool_registry(settings),
            policy_engine=build_policy_engine(),
            execution_context=ToolExecutionContext(
                environment=settings.environment,
                correlation_id=request.get("correlation_id") or str(uuid.uuid4()),
                approved=bool(request.get("approved", False)),
                change_ticket=request.get("change_ticket"),
            ),
            tool_runtime=request.get("tool_runtime", {}),
        )
        result = entrypoint(inputs, runtime)
        if not isinstance(result, dict):
            raise TypeError("crew entrypoint must return a dict")
        outputs = result.get("outputs", result)
        metadata = result.get("metadata", {}) if "outputs" in result else {}
        if not isinstance(outputs, dict) or not isinstance(metadata, dict):
            raise TypeError("crew result must be {'outputs': dict, 'metadata': dict} or a plain output dict")
        validate_contract(outputs, manifest.output_schema, label="outputs")
        print(json.dumps({"ok": True, "outputs": outputs, "metadata": metadata}, ensure_ascii=False))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc), "error_type": type(exc).__name__, "traceback": traceback.format_exc()}, ensure_ascii=False))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
