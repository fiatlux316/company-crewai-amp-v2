from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from .config.settings import Settings
from .deploy_client import deploy_package
from .local_runner import run_local_crew
from .packager import build_package


def _load_json(value: str) -> dict:
    path = Path(value)
    text = path.read_text(encoding="utf-8") if path.exists() else value
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("JSON input must be an object")
    return parsed


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="crew-dev")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("run-local")
    p.add_argument("project_dir")
    p.add_argument("--inputs", required=True)

    p = sub.add_parser("package")
    p.add_argument("project_dir")
    p.add_argument("--output", default="dist")

    p = sub.add_parser("deploy")
    p.add_argument("artifact")
    p.add_argument("--server-url", default=os.getenv("CREW_SERVER_URL", "http://localhost:8080"))
    p.add_argument("--token", default=os.getenv("CREW_DEPLOY_TOKEN"))

    args = parser.parse_args()
    if args.command == "run-local":
        outputs, metadata = run_local_crew(args.project_dir, _load_json(args.inputs), settings=Settings.from_env())
        print(json.dumps({"outputs": outputs, "metadata": metadata}, indent=2, ensure_ascii=False))
    elif args.command == "package":
        print(build_package(args.project_dir, args.output))
    elif args.command == "deploy":
        print(json.dumps(deploy_package(args.artifact, server_url=args.server_url, token=args.token), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
