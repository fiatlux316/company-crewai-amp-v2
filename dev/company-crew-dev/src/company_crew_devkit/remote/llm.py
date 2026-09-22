from __future__ import annotations

from typing import Any
import httpx
from crewai import BaseLLM


class RemoteLLMClient(BaseLLM):
    """Thin CrewAI LLM adapter. Provider credentials and model routing stay server-side."""

    def __init__(
        self,
        model_alias: str,
        *,
        gateway_url: str,
        token: str,
        timeout_seconds: float = 60.0,
    ) -> None:
        super().__init__(model=model_alias)
        self.gateway_url = gateway_url.rstrip("/")
        self.token = token
        self.timeout_seconds = timeout_seconds

    def call(
        self,
        messages: str | list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        normalized = messages if isinstance(messages, list) else [{"role": "user", "content": messages}]
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": normalized,
        }
        if tools:
            payload["tools"] = tools
        allowed_keys = {"temperature", "max_tokens", "stop", "top_p", "frequency_penalty", "presence_penalty", "seed", "response_format"}
        payload.update({k: v for k, v in kwargs.items() if k in allowed_keys and v is not None})

        response = httpx.post(
            f"{self.gateway_url}/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()


        # 기존 로직:
        # return body["choices"][0]["message"].get("content") or ""
        
        # 변경할 로직:
        message = body["choices"][0]["message"]
        content = message.get("content")
        if content:
            return content
            
        tool_calls = message.get("tool_calls")
        if tool_calls:
            import json
            tc = tool_calls[0]
            func = tc.get("function", {})
            name = func.get("name", "")
            args = func.get("arguments", "{}")
            # CrewAI가 파싱할 수 있는 ReAct 텍스트 형태로 변환 반환
            return f"Action: {name}\nAction Input: {args}"
            
        return ""