from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from company_flow_server.config.jsonc_loader import load_jsonc
from .flow_models import FlowDefinition, FlowStep


class FlowRegistry:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def load(self, flow_id: str) -> FlowDefinition:
        path = self.root / f"{flow_id}.jsonc"
        if not path.is_file():
            raise KeyError(f"flow not found: {flow_id}")
        raw: dict[str, Any] = load_jsonc(path)
        steps = tuple(
            FlowStep(
                step_id=s["step_id"], crew_id=s["crew_id"], version=s["version"],
                inputs=dict(s.get("inputs", {})),
                continue_on_error=bool(s.get("continue_on_error", False)),
            ) for s in raw["steps"]
        )
        ids = [s.step_id for s in steps]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate step_id in flow {flow_id}")
        return FlowDefinition(
            flow_id=raw["flow_id"], version=raw["version"], name=raw["name"],
            description=raw.get("description", ""), steps=steps,
            output=dict(raw.get("output", {})),
        )

    def save(self, raw: dict[str, Any]) -> Path:
        flow_id = raw["flow_id"]
        path = self.root / f"{flow_id}.jsonc"
        path.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def list(self) -> list[dict[str, Any]]:
        items = []
        for path in sorted(self.root.glob("*.jsonc")):
            try:
                raw = load_jsonc(path)
                items.append({
                    "flow_id": raw.get("flow_id", path.stem),
                    "version": raw.get("version", ""),
                    "name": raw.get("name", path.stem),
                    "description": raw.get("description", ""),
                    "steps": len(raw.get("steps", [])),
                })
            except Exception:
                continue
        return items
