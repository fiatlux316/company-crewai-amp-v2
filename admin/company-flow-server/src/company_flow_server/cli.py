from __future__ import annotations

import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from .server.executor import CrewExecutor
from .server.flow_registry import FlowRegistry
from .server.orchestrator import FlowOrchestrator
from .server.registry import CrewRegistry


def _load_json(value: str) -> dict:
    path = Path(value)
    text = path.read_text(encoding="utf-8") if path.exists() else value
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("JSON input must be an object")
    return parsed


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="flow-admin")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("serve")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", default=8080, type=int)

    p = sub.add_parser("flow-run")
    p.add_argument("flow_id")
    p.add_argument("--inputs", required=True)
    p.add_argument("--registry", default="team_registry")
    p.add_argument("--flows", default="flows")

    args = parser.parse_args()
    if args.command == "serve":
        import uvicorn
        uvicorn.run("company_flow_server.app:app", host=args.host, port=args.port, reload=False)
    elif args.command == "flow-run":
        registry = CrewRegistry(args.registry)
        flow = FlowRegistry(args.flows).load(args.flow_id)
        result = FlowOrchestrator(CrewExecutor(registry)).run(flow, _load_json(args.inputs))
        print(json.dumps({"flow_id": result.flow_id, "correlation_id": result.correlation_id, "outputs": result.outputs, "steps": result.steps}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
