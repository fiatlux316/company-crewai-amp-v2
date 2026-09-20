# company-crew-dev

개발자 전용 레포입니다. 개인 Crew의 개발, 로컬 실행, 테스트, 패키징, 팀 서버 배포만 담당합니다.

## 책임 경계
- 이 레포가 소유: `company_crew_sdk`, 로컬 개발 런타임, 개인 Crew 소스, `.crewpkg` 생성, 배포 클라이언트
- 이 레포가 모르는 것: 팀 Flow, 서버 Registry 디렉터리, Flow 실행 프로세스, 운영 서버 설정

## 개발 흐름
```bash
uv sync
uv run crew-dev run-local crew_packages/incident_analysis_crew --inputs '{"incident_id":"INC-1","symptom":"latency"}'
uv run crew-dev package crew_packages/incident_analysis_crew --output dist
uv run crew-dev deploy dist/ops.incident-analysis-1.0.0.crewpkg --server-url http://localhost:8080
```

## 서버와의 계약
Crew 소스는 개발자 DevKit이나 관리자 서버 모듈을 import하지 않습니다. 표준 entrypoint는 `run(inputs: dict, runtime) -> dict`이며, 패키지 경계는 `crew-manifest.json`의 input/output schema로 검증합니다.

즉 두 레포 사이에는 Python package dependency가 없습니다. 배포 계약은 `.crewpkg + manifest schema v1 + entrypoint protocol`뿐입니다.

## Central runtime model

LLM/tool/policy implementations are intentionally absent from this repository. Local Crew execution uses the administrator-owned LLM Gateway and MCP Server. See `REMOTE_RUNTIME.md`.

## Process visualization contract
Add `process_definition` to `crew-manifest.json` and ship a `process.jsonc`. The admin Process Console uses it to draw Task -> Agent -> Tool relationships without executing your Crew.

## MCP parameter ownership
Agent controls reasoning arguments only. `RemoteCrewRuntime` injects business scope (`system_id`, `incident_id`, `crew_id`) and the admin MCP server derives security scope from the bearer token.
