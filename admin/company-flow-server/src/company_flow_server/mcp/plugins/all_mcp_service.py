from __future__ import annotations

import os
import sys

TOOL_METADATA = {
    'name': 'all.mcp.list',
    'description': 'Retrieve all registered MCP tools and their input/output schemas.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'filter': {
                'type': 'string',
                'description': 'Optional search keyword to filter tool name or description'
            }
        },
        'required': []
    },
    'output_schema': {
        'type': 'string',
        'description': 'ToolEnvelope JSON text containing list of all registered MCP tools.'
    },
}


def register_tool(mcp_app) -> None:
    @mcp_app.tool(name=TOOL_METADATA["name"])
    def get_all_mcp_tools(filter: str = "") -> str:
        """
        Retrieve all registered MCP tools and their schemas.

        Args:
            filter: Optional keyword to filter tool names or descriptions
        """
        all_mcp_api = None
        try:
            from .base_api import all_mcp_api as api
            all_mcp_api = api
        except ImportError:
            print("Error: Could not import all_mcp_api in all_mcp_service.py", file=sys.stderr)
            return "Error: Could not import all_mcp_api"

        return all_mcp_api.get_all_mcp_list(filter)
