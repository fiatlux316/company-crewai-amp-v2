from __future__ import annotations
import os
import sys

TOOL_METADATA = {
    'name': 'jira.create_issue',
    'description': 'Create Jira Issue.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'project_key': {'type': 'string'},
            'summary': {'type': 'string'},
            'description': {'type': 'string'},
            'issue_type': {'type': 'string'},
        },
        'required': ['project_key', 'summary', 'description', 'issue_type']
    },
    'output_schema': {
        'type': 'string',
        'description': 'ToolEnvelope JSON text containing send results.'
    },
}

def register_tool(mcp_app) -> None:
    @mcp_app.tool(name=TOOL_METADATA["name"])
    def create_jira_issue(project_key: str, summary: str, description: str, issue_type: str = "Task") -> str:
        """
        Creates a new issue in Jira.
        
        Args:
            project_key: Key of the Jira project (e.g., 'PROJ')
            summary: Short summary or title of the issue
            description: Detailed description of the issue
            issue_type: Type of issue (e.g., 'Bug', 'Task', 'Story')
        """
        return f"[Jira Skeleton] Successfully created {issue_type} in project '{project_key}'. Summary: {summary}"