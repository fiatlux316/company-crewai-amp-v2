from __future__ import annotations
import os
import sys

TOOL_METADATA = {
    'name': 'datadog.logs.search',
    'description': 'Search datadog logs.',
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
    def search_datadog_logs(query: str, time_range: str, limit: int = 10) -> str:
        """
        Search and retrieve Datadog Logs.
        
        Args:
            query: The search query (e.g. 'status:error service:web-api')
            time_range: Human-readable time range (e.g. 'last 1 hour', 'last 24 hours')
            limit: Maximum number of log entries to retrieve (default 10)
        """

        datadog_api = None
        try:
            from .base_api import datadog_api as api 
            datadog_api = api
        except ImportError:
            print("Error: Could not import datadog_api in datadog_service.py", file=sys.stderr)
            return

        return datadog_api.datadog_logs_search(query, time_range, limit)
