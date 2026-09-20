from __future__ import annotations
import os
import sys

TOOL_METADATA = {
    'name': 'bitbucket.list_repositories',
    'description': 'Lists repositories in a specific Bitbucket project.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'project_key': {'type': 'string'},
        },
        'required': ['project_key']
    },
    'output_schema': {
        'type': 'string',
        'description': 'ToolEnvelope JSON text containing send results.'
    },
}

def register_tool(mcp_app) -> None:
    @mcp_app.tool(name=TOOL_METADATA["name"])
    def list_bitbucket_repositories(project_key: str) -> str:
        """
        Lists repositories in a specific Bitbucket project.
        
        Args:
            project_key: Key of the Bitbucket project (e.g. 'PROJ')
        """
        return f"[Bitbucket Skeleton] Repositories under project '{project_key}': ['auth-service', 'payment-gateway', 'monitoring-infra']"