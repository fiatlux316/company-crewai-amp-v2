from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from urllib.parse import quote

from crewai_tools import MCPServerAdapter


class RemoteMCPToolProvider:
    """Discover remote MCP tools while injecting only trusted business context.

    Parameter ownership:
      * Agent/LLM: tool arguments exposed by MCP schema (query, hours, ...)
      * Crew runtime: business context headers (system_id, incident_id, ...)
      * Server: security context derived from bearer token (role/env/permissions)
    """

    def __init__(self, *, mcp_url: str, token: str, business_context: dict[str, Any] | None = None) -> None:
        self.mcp_url = mcp_url
        self.token = token
        self.business_context = business_context or {}
        self._adapter: Any | None = None

    def __enter__(self) -> "RemoteMCPToolProvider":
        headers = {"Authorization": f"Bearer {self.token}"}
        # Explicit allow-list: these are scope inputs, not authorization claims.
        header_map = {
            "system_id": "X-Business-System-Id",
            "incident_id": "X-Business-Incident-Id",
            "crew_id": "X-Crew-Id",
        }
        for key, header in header_map.items():
            value = self.business_context.get(key)
            if value is not None:
                headers[header] = quote(str(value), safe="-_.:")

        server_params = {
            "url": self.mcp_url, 
            "headers": headers,
            "transport": "streamable-http"
        }
        self._adapter = MCPServerAdapter(server_params)
        self._adapter.__enter__()
        return self

    def tools(self, required_names: Iterable[str]) -> list[Any]:
        if self._adapter is None:
            raise RuntimeError("RemoteMCPToolProvider must be used as a context manager")

        # MCPServerAdapter 내부에서 Tool Name 정규화로 인해 Tool Name을 여기에 맞게 변환해줌
        required = list(map( lambda x : x.replace(".","_"),required_names))
        # print("required_names:", required)
        # print("tools:", self._adapter.tools)
        discovered = list(self._adapter.tools)
        # print("discovered:", discovered)
        by_name = {getattr(tool, "name", ""): tool for tool in discovered}
        # print("by_name:", by_name)
        missing = sorted(set(required) - set(by_name))
        #print("missing:", missing)
        if missing:
            raise PermissionError("MCP server did not expose required tools: " + ", ".join(missing))
        return [by_name[name] for name in required]

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._adapter is not None:
            self._adapter.__exit__(exc_type, exc, tb)
            self._adapter = None
