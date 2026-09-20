from __future__ import annotations
import os
import sys

TOOL_METADATA = {
    'name': 'confluence.search',
    'description': 'Search Confluence content.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'query': {'type': 'string'},
        },
        'required': ['query']
    },
    'output_schema': {
        'type': 'string',
        'description': 'ToolEnvelope JSON text containing send results.'
    },
}

def register_tool(mcp_app) -> None:
    @mcp_app.tool(name=TOOL_METADATA["name"])
    def search_confluence(query: str) -> str:
        """
        Searches Confluence content.
        
        Args:
            query: Confluence search query string
        """
        return f"[Confluence Skeleton] Search results for '{query}': ['Deployment Guide 2026', 'Monitoring Runbooks', 'Incident Report Template']"
