from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class FlowStep:
    step_id: str
    crew_id: str
    version: str
    inputs: dict[str, Any]
    continue_on_error: bool = False


@dataclass(frozen=True, slots=True)
class FlowDefinition:
    flow_id: str
    version: str
    name: str
    steps: tuple[FlowStep, ...]
    description: str = ""
    output: dict[str, Any] = field(default_factory=dict)
