from __future__ import annotations
import os
import sys

TOOL_METADATA = {
    'name': 'jira.get_issue',
    'description': 'Get Jira issue details.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'issue_key': {'type': 'string'},
        },
        'required': ['issue_key']
    },
    'output_schema': {
        'type': 'string',
        'description': 'ToolEnvelope JSON text containing send results.'
    },
}

def register_tool(mcp_app) -> None:
    @mcp_app.tool(name=TOOL_METADATA["name"])
    def get_jira_issue(issue_key: str) -> str:
        """
        Retrieves details of a Jira issue by its key.
        
        Args:
            issue_key: The issue key (e.g., 'PROJ-123')
        """
        return f"[Jira Skeleton] Retrieved issue {issue_key}: Summary = 'Sample Issue', Status = 'In Progress'"
