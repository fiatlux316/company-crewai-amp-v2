from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import uuid

from .executor import CrewExecutor
from .flow_models import FlowDefinition


@dataclass(slots=True)
class FlowRunResult:
    flow_id: str
    correlation_id: str
    outputs: dict[str, Any]
    steps: dict[str, dict[str, Any]] = field(default_factory=dict)


class FlowOrchestrator:
    def __init__(self, executor: CrewExecutor) -> None:
        self.executor = executor

    def run(
        self,
        flow: FlowDefinition,
        flow_inputs: dict[str, Any],
        *,
        approved: bool = False,
        change_ticket: str | None = None,
        tool_runtime: dict[str, dict[str, Any]] | None = None,
    ) -> FlowRunResult:
        correlation_id = str(uuid.uuid4())
        context: dict[str, Any] = {"flow": flow_inputs, "steps": {}}
        step_results: dict[str, dict[str, Any]] = {}

        for step in flow.steps:
            resolved_inputs = self._resolve_value(step.inputs, context)
            try:
                result = self.executor.run(
                    step.crew_id,
                    step.version,
                    resolved_inputs,
                    correlation_id=correlation_id,
                    approved=approved,
                    change_ticket=change_ticket,
                    tool_runtime=tool_runtime,
                )
                state = {"status": "succeeded", "outputs": result.outputs, "metadata": result.metadata}
            except Exception as exc:
                state = {"status": "failed", "error": str(exc), "outputs": {}}
                context["steps"][step.step_id] = state
                step_results[step.step_id] = state
                if not step.continue_on_error:
                    raise
                continue
            context["steps"][step.step_id] = state
            step_results[step.step_id] = state

        outputs = self._resolve_value(flow.output, context)
        return FlowRunResult(
            flow_id=flow.flow_id,
            correlation_id=correlation_id,
            outputs=outputs,
            steps=step_results,
        )

    def _resolve_value(self, value: Any, context: dict[str, Any]) -> Any:
        if isinstance(value, str) and value.startswith("$"):
            return self._lookup(value[1:], context)
        if isinstance(value, dict):
            return {k: self._resolve_value(v, context) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve_value(v, context) for v in value]
        return value

    @staticmethod
    def _lookup(path: str, context: dict[str, Any]) -> Any:
        current: Any = context
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                raise KeyError(f"flow reference not found: ${path}")
            current = current[part]
        return current
