from __future__ import annotations

import json
from typing import Any

def get_all_mcp_list(filter: str = "") -> str:
    """Retrieve the list of all registered MCP tools and their schemas."""
    from company_flow_server.mcp.registry import get_mcp_catalog

    catalog = get_mcp_catalog()
    if filter and filter.strip():
        f = filter.strip().lower()
        catalog = [
            tool for tool in catalog
            if f in tool.get("name", "").lower() or f in tool.get("description", "").lower()
        ]

    result = {
        "status": "success",
        "total_count": len(catalog),
        "tools": catalog
    }
    return json.dumps(result, indent=2, ensure_ascii=False)
