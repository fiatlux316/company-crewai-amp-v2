from __future__ import annotations
import os
import sys

TOOL_METADATA = {
    'name': 'teams.send',
    'description': 'Send a message using Teams webhook.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'subject': {'type': 'string'},
            'markdown_content': {'type': 'string'}
        },
        'required': ['subject','markdown_content']
    },
    'output_schema': {
        'type': 'string',
        'description': 'ToolEnvelope JSON text containing results.'
    },
}

def register_tool(mcp_app) -> None:
    @mcp_app.tool(name=TOOL_METADATA["name"])
    def send_teams_message(subject: str, markdown_content: str) -> str:
        """
        Sends a message using Teams webhook.
        Converts markdown content to formatted HTML with styling before sending.
        """
        teams_api = None
        try:
            from .base_api import teams_api as api 
            teams_api = api
        except ImportError:
            print("Error: Could not import teams_api in teams_service.py", file=sys.stderr)
            return

        return teams_api.send_teams_message(subject, markdown_content)