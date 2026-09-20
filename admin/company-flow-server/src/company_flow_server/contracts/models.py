from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CrewRunResult:
    outputs: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ServerCrewRuntime:
    settings: Any
    llms: Any
    tools: Any
    policy_engine: Any
    execution_context: Any
    tool_runtime: dict[str, dict[str, Any]] = field(default_factory=dict)
