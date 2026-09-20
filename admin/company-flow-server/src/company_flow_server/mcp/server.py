from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import unquote

from mcp.server.fastmcp import Context, FastMCP

from company_flow_server.bootstrap import build_policy_engine, build_tool_registry
from company_flow_server.policy.models import ToolExecutionContext
from company_flow_server.auth.rbac import decode_token

# FastMCP streamable-http endpoint is mounted at /mcp by the MCP runtime.
# Host/port are explicitly configured so Docker can expose :8090.
mcp = FastMCP(
    "Company Agent Runtime MCP",
    host=os.getenv("MCP_HOST", "0.0.0.0"),
    port=int(os.getenv("MCP_PORT", "8090")),
    #path="/mcp",
)
EXPOSED_TOOLS = {x.strip() for x in os.getenv("MCP_EXPOSED_TOOLS", "company.internal_search").split(",") if x.strip()}


def _headers(ctx: Context) -> dict[str, str]:
    request = getattr(getattr(ctx, "request_context", None), "request", None)
    headers = getattr(request, "headers", {}) if request is not None else {}
    return {str(k).lower(): str(v) for k, v in dict(headers).items()}


def _security_context(headers: dict[str, str]) -> dict[str, Any]:
    auth = headers.get("authorization", "")
    token = auth.removeprefix("Bearer ").strip()
    if not token:
        raise PermissionError("MCP bearer token is required")

    # Local-only compatibility mode. Production uses the same JWT verifier as the API.
    if os.getenv("AUTH_DISABLED", "false").lower() == "true":
        policies = json.loads(os.getenv("MCP_TOKEN_POLICIES", "{}"))
        return policies.get(token, {
            "user_id": "dev-admin", "roles": ["platform_admin"],
            "environment": os.getenv("COMPANY_ENV", "dev"), "allowed_systems": []
        })

    principal = decode_token(token)
    return {
        "user_id": principal.subject,
        "roles": list(principal.roles),
        "environment": principal.environment or os.getenv("COMPANY_ENV", "dev"),
        "allowed_systems": [],
    }


def _business_context(headers: dict[str, str]) -> dict[str, Any]:
    business = {}
    for k, v in headers.items():
        if k.startswith("x-business-"):
            key = k[11:].replace("-", "_")
            business[key] = unquote(v) if v else None
        elif k == "x-crew-id":
            business["crew_id"] = unquote(v) if v else None
    return business


def _invoke(tool_name: str, *, ctx: Context, business: dict[str, Any], tool_args: dict[str, Any], tool_runtime: dict[str, Any]) -> str:
    security = _security_context(_headers(ctx))
    allowed_systems = set(security.get("allowed_systems", []))
    system_id = business.get("system_id")
    if allowed_systems and system_id not in allowed_systems:
        raise PermissionError(f"system scope denied: {system_id}")

    from company_flow_server.config.settings import Settings
    registry = build_tool_registry(Settings.from_env())
    tool = registry.create(
        tool_name,
        policy_engine=build_policy_engine(),
        execution_context=ToolExecutionContext(
            user_id=str(security.get("user_id", "developer")),
            environment=str(security.get("environment", "dev")),
            correlation_id=business.get("incident_id") or "mcp-dev-session",
            approved=False,
            change_ticket=None,
        ),
        **tool_runtime,
    )
    return tool._run(**tool_args)

from company_flow_server.mcp.registry import register_all_plugins
register_all_plugins(mcp)


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
