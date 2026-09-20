from __future__ import annotations
import os
import sys

TOOL_METADATA = {
    'name': 'bitbucket.create_pull_request',
    'description': 'Creates a new Pull Request in Bitbucket.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'repo_slug': {'type': 'string'},
            'title': {'type': 'string'},
            'source_branch': {'type': 'string'},
            'destination_branch': {'type': 'string'},
        },
        'required': ['repo_slug', 'title', 'source_branch', 'destination_branch']
    },
    'output_schema': {
        'type': 'string',
        'description': 'ToolEnvelope JSON text containing send results.'
    },
}

def register_tool(mcp_app) -> None:
    @mcp_app.tool(name=TOOL_METADATA["name"])
    def create_bitbucket_pull_request(repo_slug: str, title: str, source_branch: str, destination_branch: str) -> str:
        """
        Creates a new Pull Request in Bitbucket.
        
        Args:
            repo_slug: Repository identifier slug (e.g. 'auth-service')
            title: Title of the PR
            source_branch: Source branch name (e.g. 'feature/monitoring')
            destination_branch: Target branch name (e.g. 'main')
        """
        return f"[Bitbucket Skeleton] PR '{title}' created successfully: {source_branch} -> {destination_branch} in repo '{repo_slug}'."
