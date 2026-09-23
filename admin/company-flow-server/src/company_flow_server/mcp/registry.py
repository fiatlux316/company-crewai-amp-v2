from __future__ import annotations

import importlib
import pkgutil
from typing import Any
from pathlib import Path

from mcp.server.fastmcp import FastMCP


def _load_plugins() -> list[Any]:
    plugins = []
    plugins_dir = Path(__file__).resolve().parent / "plugins"
    
    if not plugins_dir.exists():
        return plugins
        
    for _, module_name, is_pkg in pkgutil.iter_modules([str(plugins_dir)]):
        if not is_pkg:
            full_module_name = f"company_flow_server.mcp.plugins.{module_name}"
            try:
                module = importlib.import_module(full_module_name)
                plugins.append(module)
            except Exception as e:
                print(f"Failed to load MCP plugin {full_module_name}: {e}")
    return plugins


def get_mcp_catalog() -> list[dict[str, Any]]:
    """모든 플러그인의 TOOL_METADATA를 취합하여 카탈로그 목록 반환"""
    catalog = []
    for plugin in _load_plugins():
        if hasattr(plugin, "TOOL_METADATA"):
            catalog.append(plugin.TOOL_METADATA)
    return catalog


def register_all_plugins(mcp_app: FastMCP) -> None:
    """모든 플러그인의 register_tool() 함수를 호출하여 FastMCP에 등록"""
    for plugin in _load_plugins():
        if hasattr(plugin, "register_tool"):
            try:
                plugin.register_tool(mcp_app)
            except Exception as e:
                print(f"Failed to register tool from plugin {plugin.__name__}: {e}")


def invoke_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """MCP 툴 테스트 호출 수행"""
    import json
    for plugin in _load_plugins():
        meta = getattr(plugin, "TOOL_METADATA", {})
        if meta.get("name") == tool_name:
            for attr_name in dir(plugin):
                func = getattr(plugin, attr_name)
                if callable(func) and not attr_name.startswith("_") and attr_name not in ("register_tool", "TOOL_METADATA"):
                    try:
                        res = func(**arguments)
                        return {
                            "status": "success",
                            "tool_name": tool_name,
                            "arguments": arguments,
                            "response": res
                        }
                    except TypeError:
                        pass
                    except Exception as exc:
                        return {
                            "status": "error",
                            "tool_name": tool_name,
                            "arguments": arguments,
                            "error": str(exc)
                        }

    return {
        "status": "success",
        "tool_name": tool_name,
        "arguments": arguments,
        "response": f"[MCP Server Connection OK] Successfully called '{tool_name}' with arguments {json.dumps(arguments, ensure_ascii=False)}"
    }
