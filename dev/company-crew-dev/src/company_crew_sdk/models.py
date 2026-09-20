from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CrewRuntime:
    """Runtime services injected by local runner or team Flow server.

    Crew code depends only on this stable SDK surface, never on server internals.
    Concrete registry/policy implementations are intentionally typed as Any so
    the SDK does not depend on either repository's private implementation.
    """

    settings: Any
    llms: Any
    tools: Any
    policy_engine: Any
    execution_context: Any
    tool_runtime: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass(slots=True)
class CrewRunResult:
    outputs: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
