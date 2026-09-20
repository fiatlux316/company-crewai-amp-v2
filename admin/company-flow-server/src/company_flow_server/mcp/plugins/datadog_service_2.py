from __future__ import annotations
import os
import sys

TOOL_METADATA = {
    'name': 'datadog.apm.search',
    'description': 'Search datadog APM trace spans.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'query': {'type': 'string'},
            'time_range': {'type': 'string'},
            'limit': {'type': 'integer', 'minimum': 1, 'maximum': 100}
        },
        'required': ['query','time_range','limit']
    },
    'output_schema': {
        'type': 'string',
        'description': 'ToolEnvelope JSON text containing search results.'
    },
}

def register_tool(mcp_app) -> None:
    @mcp_app.tool(name=TOOL_METADATA["name"])
    def search_datadog_apm(query: str, time_range: str, limit: int = 10) -> str:
        """
        Search and retrieve Datadog APM trace spans.
        
        Args:
            query: The trace search query (e.g. 'service:payment-gateway')
            time_range: Human-readable time range (e.g. 'last 1 hour', 'last 6 hours')
            limit: Maximum number of traces/spans to retrieve (default 10)
        """

        datadog_api = None
        try:
            from .base_api import datadog_api as api 
            datadog_api = api
        except ImportError:
            print("Error: Could not import datadog_api in datadog_service.py", file=sys.stderr)
            return

        return datadog_api.datadog_apm_search(query, time_range, limit)
