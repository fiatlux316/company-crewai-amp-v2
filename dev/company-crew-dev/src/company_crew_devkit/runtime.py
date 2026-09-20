from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Any

from .remote.llm import RemoteLLMClient
from .remote.mcp import RemoteMCPToolProvider


@dataclass(slots=True)
class RemoteCrewRuntime:
    """Developer runtime. Business context is trusted input from the local run,
    while security context is never supplied by Crew code; the server derives it
    from the bearer token.
    """

    llm_gateway_url: str
    mcp_url: str
    token: str
    business_context: dict[str, Any] = field(default_factory=dict)

    def get_llm(self, alias: str) -> Any:
        return RemoteLLMClient(
            model_alias=alias,
            gateway_url=self.llm_gateway_url,
            token=self.token,
        )

    def mcp_tools(self, required_names: list[str]) -> AbstractContextManager:
        return RemoteMCPToolProvider(
            mcp_url=self.mcp_url,
            token=self.token,
            business_context=self.business_context,
        )
