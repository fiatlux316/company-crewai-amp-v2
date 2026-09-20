# Administrator-owned Runtime

This repository is the single source of truth for:

1. LLM routing and provider credentials
2. Tool implementation and tool allow-list
3. Policy and authorization rules
4. MCP exposure
5. Crew registry and Flow orchestration

Developer repositories never receive provider keys or production tool implementations.
For production, place the MCP endpoint and LLM gateway behind SSO/OAuth and replace the demo bearer-token checks.
