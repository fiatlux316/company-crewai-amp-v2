from __future__ import annotations

from collections.abc import Callable
from typing import Any
from crewai.tools import BaseTool


ToolFactory = Callable[..., BaseTool]


class ToolRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, ToolFactory] = {}

    def register(self, tool_id: str, factory: ToolFactory) -> None:
        if tool_id in self._factories:
            raise ValueError(f"duplicate tool id: {tool_id}")
        self._factories[tool_id] = factory

    def create(self, tool_id: str, **kwargs: Any) -> BaseTool:
        try:
            factory = self._factories[tool_id]
        except KeyError as exc:
            raise KeyError(f"unknown tool id: {tool_id}") from exc
        return factory(**kwargs)

    def create_many(self, tool_ids: list[str], **kwargs: Any) -> list[BaseTool]:
        return [self.create(tool_id, **kwargs) for tool_id in tool_ids]
