# Two-repository CrewAI architecture

## 1. company-crew-dev
Developer-owned repository.

- Owns Crew/Agent/Task/Prompt source
- Runs Crew locally
- Uses administrator LLM Gateway remotely
- Discovers tools through administrator MCP Server
- Contains no LLM provider credentials, Tool implementations, or Policy Engine
- Packages `.crewpkg` and deploys it through the administrator API

## 2. company-flow-server
Administrator-owned repository.

- Owns LLM providers and model routing
- Owns Tool implementations
- Owns Policy/authorization rules
- Owns MCP exposure allow-list
- Owns Crew Registry, Flow Registry, Flow execution
- Owns deployment/runtime secrets

## Runtime boundary

Developer PC -> LLM Gateway (`/v1/chat/completions`)
Developer PC -> MCP Server (centrally exposed tools only)
Developer deployment -> `.crewpkg` -> Flow Server Registry
Production Flow -> deployed Crew -> administrator ServerRuntime -> local LLM/Tools/Policy

A Crew requesting a tool never grants itself permission. The administrator MCP exposure and server-side policy are authoritative.

## Crew Process Console
The admin server root (`/`) serves a deployed Crew catalog. Selecting a Crew opens the right-side process panel showing Task -> Agent -> Tool relationships. Developers publish `process.jsonc` inside the Crew package; the admin server renders this contract without importing/executing Crew Python.

## Three-layer MCP parameters
1. Reasoning parameters (e.g. query, hours) are exposed in the MCP tool schema and selected by the Agent.
2. Business context (e.g. system_id, incident_id, crew_id) is injected by RemoteCrewRuntime as MCP request headers.
3. Security context (user, roles, environment, allowed systems) is derived only on the admin MCP server from the bearer token. Crew code cannot claim admin/prod privileges.


## Flow Designer

`company-flow-server` owns the visual Flow Designer. Developers deploy immutable `.crewpkg` artifacts; administrators compose the deployed versions into Flow definitions. The browser never imports or executes developer Python code.

```text
Crew Catalog -> Flow Designer -> Validate -> flows/<flow_id>.jsonc
                                      |
                                      v
                                FlowOrchestrator
                                      |
                         Crew A -> Crew B -> Crew C
```

Input mappings use `$flow.*` for initial flow inputs and `$steps.<step>.outputs.*` for prior Crew outputs.

## Crew Operations Administration

Administrator-owned operational state is separated from immutable Crew packages:

```text
.crewpkg deployment ---> CrewRegistry (immutable versioned code)
                              |
Crew Admin UI ---> Admin State Store
                  |-- schedule by crew_id
                  |-- default kickoff inputs
                  |-- metadata overrides
                  `-- run history / verbose
                              |
                       Multi-worker Executor
```

Because schedule/default-input/metadata state is keyed by `crew_id` under `ADMIN_STATE_ROOT`, redeploying a Crew package or deploying a new version does not overwrite the administrator's existing schedule.

The MCP Catalog is exposed at `/api/v1/mcp/tools`; interactive FastAPI Swagger documentation is exposed at `/docs`.


## Distributed runtime

```text
                    Admin Browser
                         |
                    FastAPI API x N
                         |
              +----------+----------+
              |                     |
          PostgreSQL              Redis
   settings/schedule/history     Celery broker
              |                     |
      Distributed Scheduler          +----> Worker 1 ----> Crew subprocess
       DB unique minute claim        +----> Worker 2 ----> Crew subprocess
                                     +----> Worker N ----> Crew subprocess
                                              |
                                      shared Crew Registry
```

PostgreSQL is the source of truth for mutable administrator state. Crew deployment artifacts remain immutable/versioned. Redis carries execution jobs; workers can be horizontally scaled. Schedule state is preserved independently of Crew redeployment.


## Authentication / authorization boundary

```text
Corporate IdP / OIDC
        |
      JWT
        v
 FastAPI Authentication
        |
 Principal(sub, roles, scopes)
        |
      RBAC
   +----+-----+
   |          |
 Crew Owner  Platform/Operator/Flow Admin
   |          |
   +---- Policy authorization ----+
                                  |
                     API / Queue / Tool runtime
                                  |
                         PostgreSQL Audit Log
```

Authentication proves identity; RBAC controls platform operations; Tool Policy remains a separate server-side authorization layer for actual MCP/production actions. Client-side UI hiding is never treated as authorization.

## Dedicated Streamable HTTP MCP runtime

```text
Developer run-local
   |  COMPANY_MCP_URL=http://localhost:8090/mcp
   |  Bearer JWT + business context headers
   v
MCP service :8090 /mcp
   -> JWT authentication
   -> Tool exposure allow-list
   -> Tool Policy
   -> administrator Tool Registry
```

The MCP process is separate from the FastAPI admin API (:8080), Celery workers, scheduler and Flower.
