# company-flow-server

팀 관리자 전용 레포입니다. 배포된 Crew Registry, Flow 정의, Crew 실행 격리, 서버 기동을 담당합니다.

## 책임 경계
- 이 레포가 소유: Crew Registry, Flow JSONC, Flow Orchestrator, Worker/Executor, 운영 Runtime, 서버/API
- 이 레포가 모르는 것: 개인 Crew의 Agent/Task 구현, 개발자 로컬 프로젝트
- 개인 Crew와의 계약: `.crewpkg` + `crew-manifest.json` + `run(inputs, runtime) -> dict` 프로토콜

## 서버 기동
```bash
uv sync
uv run flow-admin serve --host 0.0.0.0 --port 8080
```

## Crew 배포 API
개발자 CLI가 다음 API로 `.crewpkg`를 전송합니다.
`POST /api/v1/crews/deploy`

## Flow 실행 API
`POST /api/v1/flows/{flow_id}/run`

## 운영 원칙
- Production Flow는 Crew 버전을 `latest`로 참조하지 않고 정확한 버전을 pin 합니다.
- 배포된 Crew 코드는 Flow process에 static import하지 않고 subprocess worker에서 실행합니다.
- 향후 subprocess executor는 Kubernetes Job executor로 교체할 수 있습니다.

## Central runtime ownership

This server owns LLM providers, tool implementations, policy enforcement and MCP exposure. Developers only receive remote clients. Start the MCP process with `company-mcp` and the Flow/API process with `flow-admin serve`.

## Process Console
Start the server and open `http://localhost:8080/`. The left pane lists deployed Crew versions; selecting one opens the right process panel with Task, Agent and Tool relationships. The graph is read from the deployed Crew's `process.jsonc` contract.


## Flow Designer

The admin console now has two tabs:

- **Crew Process**: inspect a deployed Crew's Task -> Agent -> Tool graph.
- **Flow Designer**: compose deployed, version-pinned Crews into a sequential team Flow.

Start the server and open `http://localhost:8080/`. In Flow Designer:

1. Select Crews from **Crew Catalog**.
2. Select a Crew node and edit its `step_id` and input mapping.
3. Reference flow inputs with `$flow.<name>`.
4. Reference a previous Crew output with `$steps.<step_id>.outputs.<name>`.
5. Click **Validate** and then **Save**.

Saved definitions are written to the administrator-owned `flows/<flow_id>.jsonc` directory. The server validates that every pinned Crew version is deployed and that step references point backward to a previously defined step.

Production recommendation: protect the Save API with `CREW_DEPLOY_TOKEN` or replace it with your corporate OAuth/RBAC layer.


## Node Flow Designer v2

The Flow Designer is now a node-based canvas:

- Drag a deployed Crew from the catalog onto the canvas.
- Drag Crew nodes to arrange the process visually.
- Each node shows its declared input/output ports from `crew-manifest.json`.
- Select a node and use **Recommend from previous** to query schema-aware connection suggestions.
- Recommendations score exact field-name/type matches highest and support compatible `integer -> number`.
- Applying a recommendation writes a runtime mapping such as `$steps.analyze.outputs.analysis`.
- **Validate** checks required target inputs, missing source outputs, type mismatches, deployed Crew versions, and backward-only step references.
- **Auto Layout** arranges the current nodes.
- **Save** persists the executable Flow definition. Canvas coordinates are intentionally presentation-only and are not required by the runtime.

The recommendation API is:
`GET /api/v1/schema/recommend?source_crew_id=...&source_version=...&target_crew_id=...&target_version=...`

## Crew Management Console

The Crew Management tab now provides administrator operations per deployed Crew:

- Persistent cron schedule (`minute hour day month weekday`). Schedule state is stored under `ADMIN_STATE_ROOT`, keyed by `crew_id`, and is not overwritten by package redeployment.
- Delete a deployed Crew version with explicit confirmation.
- Immediate asynchronous kickoff through a configurable worker pool (`CREW_MAX_WORKERS`, default 4).
- Persistent execution history with inputs, outputs, status, error, and captured worker verbose/stdout/stderr.
- Delete execution history with explicit confirmation.
- Editable default kickoff inputs.
- Administrator metadata overrides such as owner and deployment date display.
- MCP Catalog showing tool name and input/output schemas.
- Swagger UI at `/docs` and ReDoc at `/redoc`.

For production, replace the demo bearer-token gate with corporate OAuth/RBAC and replace JSON state files with a transactional database / scheduler store when running multiple server replicas.


## Distributed Docker Compose runtime

The administrator stack now uses:

- **PostgreSQL**: administrator-owned Crew settings, schedules, default inputs, metadata overrides, and execution history.
- **Redis**: Celery broker/result transport.
- **Celery workers**: distributed multi-worker Crew kickoff execution.
- **Distributed scheduler**: polls PostgreSQL schedules and uses a unique `(crew_id, minute_key)` DB claim so multiple scheduler replicas do not enqueue the same Crew twice for a minute.
- **API/UI**: FastAPI admin console, Flow Designer, MCP catalog and Swagger.
- **Flower**: Celery worker/task monitoring at port 5555.

### Start everything

```bash
cp .env.example .env
# Edit secrets / LLM settings in .env
docker compose up --build -d
docker compose ps
```

Admin UI / API: `http://localhost:8080/`  
Swagger: `http://localhost:8080/docs`  
Flower: `http://localhost:5555`

### Scale workers

```bash
docker compose up -d --scale worker=3
```

Each worker also supports internal Celery concurrency through `WORKER_CONCURRENCY`. For predictable resource isolation, prefer more worker containers with modest per-container concurrency.

### Persistence and redeploy behavior

Crew packages live on the shared `crew_registry` Docker volume. Administrator state lives in PostgreSQL keyed by `crew_id`; therefore schedules/default inputs/metadata are not overwritten by a Crew package redeployment or version upgrade.

### Production notes

The Compose file is an integrated team-server deployment. For production, use managed PostgreSQL/Redis where possible, rotate credentials, add corporate OAuth/RBAC, TLS/reverse proxy, backups, and migration tooling such as Alembic. The DB scheduler claim provides duplicate-enqueue protection, but Crew actions should still be designed idempotently because distributed queues are at-least-once systems.


## Authentication and RBAC

All operational APIs now use Bearer JWT authentication. For local Docker development `.env.example` defaults to `AUTH_DISABLED=true`, which creates a synthetic `platform_admin`. **Never use that setting in production.**

Built-in roles:

| Role | Purpose |
|---|---|
| `viewer` | read Crew/run/MCP/Flow information |
| `developer` | viewer + Crew deploy + DEV kickoff |
| `crew_owner` | developer + settings for Crews whose manifest owner equals JWT `sub` |
| `operator` | operational kickoff including PROD + Flow run |
| `flow_admin` | create/update/run Flows |
| `platform_admin` | all permissions including destructive operations and audit |

JWT claims:
```json
{"sub":"user01","roles":["crew_owner"],"scope":"mcp:read","environment":"dev"}
```

Production should validate RS256 tokens issued by the corporate IdP using `AUTH_JWT_PUBLIC_KEY`, `AUTH_JWT_ISSUER`, and `AUTH_JWT_AUDIENCE`. The included HS256 mode is intended for isolated development/testing only.

Important controls:
- Production kickoff requires `crew:kickoff:prod`.
- Crew-owner settings changes additionally compare JWT `sub` with the immutable manifest `owner`.
- Crew delete and run-history delete remain destructive elevated operations.
- Deploy, settings change, kickoff, Crew delete and Flow save are written to PostgreSQL `audit_logs`.
- `GET /api/v1/auth/me` shows the resolved identity.
- `GET /api/v1/audit` is restricted to `audit:read` / platform admin.

For enterprise deployment, put the service behind your SSO/OIDC gateway and map corporate groups to these application roles.

## Streamable HTTP MCP service (:8090)

The Docker Compose stack now includes a dedicated `mcp` service. It runs `company-mcp` using FastMCP Streamable HTTP on `0.0.0.0:8090`; the developer endpoint remains:

```text
http://localhost:8090/mcp
```

Start and verify:

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
curl -i http://localhost:8090/mcp
```

A plain curl may return an MCP protocol error because `/mcp` expects MCP Streamable HTTP requests; a 404 means the MCP service/path is not mounted correctly. Local `crew-dev run-local` uses `MCPServerAdapter` and sends the bearer token plus `X-Business-System-Id`, `X-Business-Incident-Id`, and `X-Crew-Id` headers.

In production set `AUTH_DISABLED=false`; MCP validates the same JWT used by the admin API before invoking administrator-owned Tool Registry / Policy Engine logic.
