from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from company_flow_server.contracts.validation import validate_contract
from company_flow_server.contracts.models import CrewRunResult

from .registry import CrewRegistry


class CrewExecutor:
    """Executes a deployed Crew in a subprocess boundary.

    This prevents a personal Crew module from being statically imported by the Flow
    process. For stronger production isolation, replace this executor with a container
    or job-runner implementation while keeping the same interface.
    """

    def __init__(self, registry: CrewRegistry, *, timeout_seconds: int = 900) -> None:
        self.registry = registry
        self.timeout_seconds = timeout_seconds

    def run(
        self,
        crew_id: str,
        version: str,
        inputs: dict[str, Any],
        *,
        correlation_id: str,
        approved: bool = False,
        change_ticket: str | None = None,
        tool_runtime: dict[str, dict[str, Any]] | None = None,
    ) -> CrewRunResult:
        deployed = self.registry.resolve(crew_id, version)
        manifest = self.registry.manifest(crew_id, version)
        validate_contract(inputs, manifest.input_schema, label="inputs")

        request = {
            "inputs": inputs,
            "correlation_id": correlation_id,
            "approved": approved,
            "change_ticket": change_ticket,
            "tool_runtime": tool_runtime or {},
        }
        env = dict(os.environ)
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "company_flow_server.server.worker",
                "--deployed-dir",
                str(deployed),
            ],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            env=env,
            check=False,
        )
        stdout = proc.stdout.strip().splitlines()
        if not stdout:
            raise RuntimeError(f"crew worker produced no output; stderr={proc.stderr.strip()}")
        payload = json.loads(stdout[-1])
        if proc.returncode != 0 or not payload.get("ok"):
            raise RuntimeError(
                f"crew {crew_id}@{version} failed: {payload.get('error', proc.stderr.strip())}"
            )
        outputs = payload["outputs"]
        validate_contract(outputs, manifest.output_schema, label="outputs")
        metadata = dict(payload.get("metadata", {}))
        verbose = list(metadata.get("verbose", [])) if isinstance(metadata.get("verbose", []), list) else []
        verbose.extend(stdout[:-1])
        if proc.stderr.strip(): verbose.extend(proc.stderr.strip().splitlines())
        metadata["verbose"] = verbose
        return CrewRunResult(outputs=outputs, metadata=metadata)
