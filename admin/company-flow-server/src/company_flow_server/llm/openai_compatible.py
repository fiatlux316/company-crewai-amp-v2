from __future__ import annotations

import json
from typing import Any
import httpx

from .base import CompanyBaseLLM

class OpenAICompatibleCompanyLLM(CompanyBaseLLM):
    """Adapter for an internal OpenAI-compatible Chat Completions gateway.
    Tool-calling response translation is intentionally kept in this adapter so crews remain provider-neutral.
    """

    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        api_key: str,
        timeout_seconds: float = 30.0,
        temperature: float | None = 0.0,
    ) -> None:
        super().__init__(model=model, temperature=temperature)
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _normalize_messages(messages: str | list[dict[str, str]]) -> list[dict[str, str]]:
        if isinstance(messages, str):
            return [{"role": "user", "content": messages}]
        return messages

    def call(
        self,
        messages: str | list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str | Any:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._normalize_messages(messages),
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        if tools:
            payload["tools"] = tools

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-litellm-api-key"] = self.api_key
            #headers["Authorization"] = f"Bearer {self.api_key}"

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=payload
            )
            response.raise_for_status()
            body = response.json()

        message = body["choices"][0]["message"]
        # CrewAI versions differ in native tool-call plumbing. For company runtime portability,
        # execute a provider tool call here only when CrewAI supplies the function registry.
        tool_calls = message.get("tool_calls") or []
        if tool_calls and available_functions:
            results: list[str] = []
            for item in tool_calls:
                fn = item["function"]
                name = fn["name"]
                args = json.loads(fn.get("arguments") or "{}")
                if name not in available_functions:
                    raise ValueError(f"LLM requested unregistered function: {name}")
                results.append(str(available_functions[name](**args)))
            return "\n".join(results)

        return message.get("content") or ""

    def supports_function_calling(self) -> bool:
        return True

    def supports_stop_words(self) -> bool:
        return True
