from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any


class _LocalToolProvider(AbstractContextManager):
    def __init__(self, runtime: "ServerCrewRuntime", required_names: list[str]) -> None:
        self.runtime = runtime
        self.required_names = required_names

    def __enter__(self) -> "_LocalToolProvider":
        return self

    def tools(self, required_names: list[str]) -> list[Any]:
        return [
            self.runtime.tools.create(
                name,
                policy_engine=self.runtime.policy_engine,
                execution_context=self.runtime.execution_context,
                **dict(self.runtime.tool_runtime.get(name, {})),
            )
            for name in required_names
        ]

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        return None


@dataclass(slots=True)
class ServerCrewRuntime:
    settings: Any
    llms: Any
    tools: Any
    policy_engine: Any
    execution_context: Any
    tool_runtime: dict[str, dict[str, Any]]

    def get_llm(self, alias: str) -> Any:
        return self.llms.get(alias)

    def mcp_tools(self, required_names: list[str]) -> _LocalToolProvider:
        # Same Crew-facing contract as the developer RemoteCrewRuntime, but no
        # network hop is required inside the trusted server boundary.
        return _LocalToolProvider(self, required_names)
