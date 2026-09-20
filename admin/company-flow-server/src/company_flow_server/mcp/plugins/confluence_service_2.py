from __future__ import annotations
import os
import sys

TOOL_METADATA = {
    'name': 'confluence.create_page',
    'description': 'Creates a new Confluence page.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'space_key': {'type': 'string'},
            'title': {'type': 'string'},
            'body_content': {'type': 'string'},
            'parent_page_id': {'type': 'string'},
        },
        'required': ['space_key', 'title', 'body_content']
    },
    'output_schema': {
        'type': 'string',
        'description': 'ToolEnvelope JSON text containing send results.'
    },
}

def register_tool(mcp_app) -> None:
    @mcp_app.tool(name=TOOL_METADATA["name"])
    def create_confluence_page(space_key: str, title: str, body_content: str, parent_page_id: str = None) -> str:
        """
        Creates a new wiki page in Confluence.
        
        Args:
            space_key: Space key of Confluence (e.g. 'DEVOPS')
            title: Title of the page
            body_content: Content of the page
            parent_page_id: Optional ID of the parent page
        """
        return f"[Confluence Skeleton] Created page '{title}' in space '{space_key}' with body size {len(body_content)} bytes."