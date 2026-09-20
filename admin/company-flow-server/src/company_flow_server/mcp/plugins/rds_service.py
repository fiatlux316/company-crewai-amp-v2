from __future__ import annotations
import os
import sys

TOOL_METADATA = {
    'name': 'rds.execute_query',
    'description': 'Execute read-only SQL query on RDS.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'db_identifier': {'type': 'string'},
            'query': {'type': 'string'}
        },
        'required': ['db_identifier','query']
    },
    'output_schema': {
        'type': 'string',
        'description': 'ToolEnvelope JSON text containing results.'
    },
}

def register_tool(mcp_app) -> None:
    @mcp_app.tool(name=TOOL_METADATA["name"])
    def execute_rds_query(db_identifier: str, query: str) -> str:
        """
        Executes a read-only SQL query on the specified RDS database instance.
        
        Args:
            db_identifier: The RDS DB Instance identifier or connection name
            query: The SQL query to execute (must be SELECT/read-only)
        """
        # Safety check to prevent write queries in this tool
        cleaned_query = query.strip().upper()
        if not cleaned_query.startswith("SELECT"):
            return "Error: Only read-only SELECT queries are allowed for security reasons."
            
        return f"[RDS Skeleton] Successfully connected to RDS database '{db_identifier}' and executed: '{query}'\nResult: 5 rows found."
