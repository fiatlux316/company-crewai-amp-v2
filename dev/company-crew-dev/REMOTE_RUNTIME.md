# Remote Runtime Contract

The developer repository contains no LLM provider, tool implementation, or policy engine.

- LLM: `RemoteLLMClient` -> administrator `/v1/chat/completions`
- Tools: `RemoteMCPToolProvider` -> administrator MCP server
- Policy: enforced only on administrator infrastructure
- Crew source requests tools by name; naming a tool never grants permission

Local development requires only `COMPANY_RUNTIME_URL`, `COMPANY_MCP_URL`, and a developer access token.

## MCP local connectivity

`COMPANY_MCP_URL=http://localhost:8090/mcp` targets the administrator Docker Compose `mcp` service. Start the admin stack before `run-local`.

The sample incident Crew should be launched with a `system_id`, because `company.internal_search` intentionally requires server-injected business scope:

```bash
uv run crew-dev run-local crew_packages/incident_analysis_crew \
  --inputs '{"incident_id":"INC-001","system_id":"ORDER","symptom":"timeout"}'
```

The Agent chooses only MCP schema parameters such as `query` and `hours`; `system_id`, incident/crew context and JWT identity are injected outside the Agent.
