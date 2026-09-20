from __future__ import annotations
import os
import sys

TOOL_METADATA = {
    'name': 'gmail.send',
    'description': 'Send an email using Gmail SMTP server.',
    'input_schema': {
        'type': 'object',
        'properties': {
            'subject': {'type': 'string'},
            'markdown_content': {'type': 'string'},
            'to_email': {'type': 'string'}
        },
        'required': ['subject','markdown_content','to_email']
    },
    'output_schema': {
        'type': 'string',
        'description': 'ToolEnvelope JSON text containing send results.'
    },
}

def register_tool(mcp_app) -> None:
    @mcp_app.tool(name=TOOL_METADATA["name"])
    def send_google_email(subject: str, markdown_content: str, to_email: str = None) -> str:
        """
        Sends an email using Gmail SMTP server.
        Converts markdown content to formatted HTML with styling before sending.
        If to_email is not provided, it defaults to the configured RECIPIENT_EMAIL environment variable.
        """
        recipient = to_email or os.environ.get("RECIPIENT_EMAIL", "").strip()
        if not recipient:
            return "Fail: RECIPIENT_EMAIL environment variable is not set and to_email was not provided."

        email_api = None
        try:
            from .base_api import email_api as api
            email_api = api
        except ImportError:
            print("Error: Could not import email_api in email_service.py", file=sys.stderr)
            return

        return email_api.send_google_email(subject, markdown_content, recipient)


