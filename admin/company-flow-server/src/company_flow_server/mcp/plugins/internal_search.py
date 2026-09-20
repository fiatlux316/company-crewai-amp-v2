from __future__ import annotations
import os
from mcp.server.fastmcp import Context

TOOL_METADATA = {
    'name': 'company.internal_search',
    'description': 'Search operational evidence within server-injected system scope.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'query': {'type': 'string'},
            'hours': {'type': 'integer', 'minimum': 1, 'maximum': 24}
        },
        'required': ['query']
    },
    'output_schema': {
        'type': 'string',
        'description': 'ToolEnvelope JSON text containing search results.'
    },
}

def register_tool(mcp_app) -> None:
    @mcp_app.tool(name=TOOL_METADATA["name"])
    def internal_search(query: str, hours: int = 1, ctx: Context | None = None) -> str:
        """Search operational evidence. Agent owns query/hours; runtime injects system scope."""
        # 런타임 순환참조 방지를 위해 실행 시점에 임포트
        from company_flow_server.mcp.server import _business_context, _headers
        import os
        import requests
        import json

        if ctx is None:
            raise RuntimeError("MCP request context is required")
        business = _business_context(_headers(ctx))
        system_id = business.get("system_id")
        if not system_id:
            raise ValueError("system_id business context is required")
        
        hours = max(1, min(int(hours), 24))
        base_url = os.getenv("INTERNAL_SEARCH_BASE_URL", "http://internal-search:9000")
        
        url = f"{base_url}/search/{system_id}"
        
        try:
            response = requests.get(url, params={"q": f"last_hours:{hours} {query}"}, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            # 여기서 데이터를 원하는 대로 가공할 수 있습니다.
            return f"Search Results for {system_id}:\n{json.dumps(data, indent=2, ensure_ascii=False)}"
        except requests.exceptions.RequestException as e:
            return f"Error executing search: {str(e)}"
