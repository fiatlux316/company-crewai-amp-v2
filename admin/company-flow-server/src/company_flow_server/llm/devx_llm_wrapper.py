from __future__ import annotations

import json
from typing import Any
import httpx

from .base import CompanyBaseLLM


class CompanyLLMWrapper(CompanyBaseLLM):
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
        formatted_messages = []
        if isinstance(messages, str):
            formatted_messages = [{"role": "user", "content": messages}]
        else:
            for msg in messages:
                content = msg.get("content", "")
                if not isinstance(content, str):
                    content = str(content)
                formatted_messages.append({
                    "role": msg.get("role", "user"),
                    "content": content
                })
        return formatted_messages

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

        # Bedrock 모델은 현재 이 게이트웨이에서 temperature 관련 필드를 전달하면 실패합니다.
        if self.temperature is not None and not (isinstance(self.model, str) and self.model.startswith("bedrock/")):
            payload["temperature"] = self.temperature
            
        if tools:
            payload["tools"] = tools

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-litellm-api-key"] = self.api_key

        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(self.base_url, headers=headers, json=payload)
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
