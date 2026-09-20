from __future__ import annotations

from abc import abstractmethod
from typing import Any

from crewai.llms.base_llm import BaseLLM


class CompanyBaseLLM(BaseLLM):
    """Stable company-owned LLM interface. CrewAI-specific changes stop here."""

    def __init__(self, model: str, temperature: float | None = None) -> None:
        super().__init__(model=model, temperature=temperature)

    @abstractmethod
    def call(
        self,
        messages: str | list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str | Any:
        raise NotImplementedError
