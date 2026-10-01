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


def _resolve_inputs(project_dir: str | Path, inputs_arg: str | None) -> dict:
    if inputs_arg:
        return _load_json(inputs_arg)

    project = Path(project_dir).resolve()

    candidates: list[Path] = []
    manifest_path = project / "crew-manifest.json"
    if manifest_path.exists():
        try:
            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            entrypoint = manifest_data.get("entrypoint", "")
            if ":" in entrypoint:
                module_name = entrypoint.split(":", 1)[0]
                pkg_name = module_name.split(".", 1)[0]
                candidates.append(project / "src" / pkg_name / "inputs.json")
        except Exception:
            pass

    candidates.extend([
        #project / "inputs.json",
        project / "src" / "inputs.json",
    ])

    for candidate in candidates:
        if candidate.is_file():
            text = candidate.read_text(encoding="utf-8")
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError(f"JSON input in {candidate} must be an object")
            return parsed

    raise FileNotFoundError(
        f"No inputs specified and no inputs.json found in candidate paths: {[str(c) for c in candidates]}"
    )


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="crew-dev")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("run-local")
    p.add_argument("project_dir")
    p.add_argument("--inputs", default=None, help="Inline JSON string or path to JSON inputs file")

    p = sub.add_parser("package")
    p.add_argument("project_dir")
    p.add_argument("--output", default="dist")

    p = sub.add_parser("deploy")
    p.add_argument("artifact")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing crew deployment if version matches")
    p.add_argument("--server-url", default=os.getenv("CREW_SERVER_URL", "http://localhost:8080"))
    p.add_argument("--token", default=os.getenv("CREW_DEPLOY_TOKEN"))

    args = parser.parse_args()
    if args.command == "run-local":

        # --inputs 에 입력 값이 오면 해당 값으로 설정하고, 없으면 src 하위에 inputs.json 을 을 참조한다.
        inputs = _resolve_inputs(args.project_dir, args.inputs)
        outputs, metadata = run_local_crew(args.project_dir, inputs, settings=Settings.from_env())
        print(json.dumps({"outputs": outputs, "metadata": metadata}, indent=2, ensure_ascii=False))
    elif args.command == "package":
        print(build_package(args.project_dir, args.output))
    elif args.command == "deploy":
        print(json.dumps(deploy_package(args.artifact, server_url=args.server_url, token=args.token, overwrite=args.overwrite), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
