from __future__ import annotations

from .config.settings import Settings
from .llm.llm_adapter import DynamicLLMAdapter
from .llm.registry import LLMRegistry
from .policy.engine import PolicyEngine, ToolPolicy
from .policy.models import RiskLevel
from .tools.http_json import InternalSearchTool
from .tools.registry import ToolRegistry


def build_llm_registry(settings: Settings) -> LLMRegistry:
    registry = LLMRegistry()
    registry.register(
        "company/devx-llm",
        lambda: DynamicLLMAdapter(
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            timeout_seconds=settings.llm_timeout_seconds,
            temperature=0.0,
        ),
    )
    return registry


def build_policy_engine() -> PolicyEngine:
    return PolicyEngine(
        {
            "company:internal_search": ToolPolicy(risk_level=RiskLevel.READ_ONLY),
            "company:restart_service": ToolPolicy(
                risk_level=RiskLevel.MEDIUM,
                requires_change_ticket_in_prod=True,
            ),
        }
    )


class _MockFastMCP:
    def __init__(self):
        self.captured = {}
    def tool(self, name: str):
        def decorator(fn):
            self.captured[name] = fn
            return fn
        return decorator

def build_tool_registry(settings: Settings) -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        "company:internal_search", 
        lambda **kwargs: InternalSearchTool(base_url=settings.internal_search_base_url, **kwargs)
    )
    registry.register(
        "company.internal_search", 
        lambda **kwargs: InternalSearchTool(base_url=settings.internal_search_base_url, **kwargs)
    )

    try:
        from crewai.tools import tool
        from company_flow_server.mcp.registry import _load_plugins
        mock_mcp = _MockFastMCP()
        for plugin in _load_plugins():
            if hasattr(plugin, "register_tool"):
                try:
                    plugin.register_tool(mock_mcp)
                except Exception:
                    pass
        for tool_name, fn in mock_mcp.captured.items():
            def make_factory(f, n):
                return lambda **kwargs: tool(n)(f)
            try:
                registry.register(tool_name, make_factory(fn, tool_name))
            except ValueError:
                pass
    except Exception as e:
        print(f"Failed to load MCP plugins: {e}")

    return registry
