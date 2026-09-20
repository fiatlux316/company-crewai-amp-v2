from __future__ import annotations

from collections.abc import Callable
from crewai.llms.base_llm import BaseLLM


LLMFactory = Callable[[], BaseLLM]


class LLMRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, LLMFactory] = {}

    def register(self, llm_id: str, factory: LLMFactory) -> None:
        if llm_id in self._factories:
            raise ValueError(f"duplicate llm id: {llm_id}")
        self._factories[llm_id] = factory

    def get(self, llm_id: str) -> BaseLLM:
        try:
            return self._factories[llm_id]()
        except KeyError as exc:
            raise KeyError(f"unknown llm id: {llm_id}") from exc
