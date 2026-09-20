from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
from typing import Any

from company_crew_sdk.contracts import validate_contract
from company_crew_sdk.manifest import CrewManifest

from .config.settings import Settings
from .runtime import RemoteCrewRuntime


def run_local_crew(
    project_dir: str | Path,
    inputs: dict[str, Any],
    *,
    settings: Settings | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    project = Path(project_dir).resolve()
    manifest = CrewManifest.load(project / "crew-manifest.json")
    validate_contract(inputs, manifest.input_schema, label="inputs")

    src = str(project / "src")
    sys.path.insert(0, src)
    try:
        module_name, callable_name = manifest.entrypoint.split(":", 1)
        entrypoint = getattr(importlib.import_module(module_name), callable_name)
        cfg = settings or Settings.from_env()
        runtime = RemoteCrewRuntime(
            llm_gateway_url=cfg.runtime_url,
            mcp_url=cfg.mcp_url,
            token=cfg.access_token,
            business_context={
                "crew_id": manifest.crew_id,
                "system_id": inputs.get("system_id"),
                "incident_id": inputs.get("incident_id"),
            },
        )
        result = entrypoint(inputs, runtime)
        if not isinstance(result, dict):
            raise TypeError("crew entrypoint must return a dict")
        outputs = result.get("outputs", result)
        metadata = result.get("metadata", {}) if "outputs" in result else {}
        if not isinstance(outputs, dict) or not isinstance(metadata, dict):
            raise TypeError("crew result must be {'outputs': dict, 'metadata': dict} or a plain output dict")
        validate_contract(outputs, manifest.output_schema, label="outputs")
        json.dumps(outputs)
        return outputs, metadata
    finally:
        if sys.path and sys.path[0] == src:
            sys.path.pop(0)
