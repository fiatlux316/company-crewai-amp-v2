from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


def _jsonc(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"(^|\s)//.*$", r"\1", text, flags=re.M)
    return json.loads(text)


def build_crew_graph(deployment_dir: Path) -> dict[str, Any]:
    """Build a UI graph from the deployed, developer-owned process definition.

    process.jsonc is the explicit contract for visualization. Agent/task config is
    enriched when available; the server never imports Crew Python just to draw it.
    """
    manifest_raw = json.loads((deployment_dir / "crew-manifest.json").read_text(encoding="utf-8"))
    process_rel = manifest_raw.get("process_definition")
    src = deployment_dir / "src"
    process_files = [deployment_dir / process_rel] if process_rel else list(src.rglob("process.jsonc"))
    if not process_files or not process_files[0].is_file():
        return {"process": "unknown", "nodes": [], "edges": [], "warning": "process.jsonc not supplied"}

    process = _jsonc(process_files[0])
    agent_files = list(src.rglob("agents.jsonc"))
    task_files = list(src.rglob("tasks.jsonc"))
    agents = _jsonc(agent_files[0]) if agent_files else {}
    tasks = _jsonc(task_files[0]) if task_files else {}

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(node_id: str, node_type: str, label: str, detail: dict[str, Any]) -> None:
        if node_id not in seen:
            nodes.append({"id": node_id, "type": node_type, "label": label, "detail": detail})
            seen.add(node_id)

    for item in process.get("tasks", []):
        tid = str(item["id"])
        aid = str(item["agent"])
        add(f"task:{tid}", "task", tid, tasks.get(tid, {}))
        acfg = agents.get(aid, {})
        add(f"agent:{aid}", "agent", acfg.get("role", aid), {"id": aid, **acfg})
        edges.append({"source": f"task:{tid}", "target": f"agent:{aid}", "label": "assigned"})
        tool_names = item.get("tools") or acfg.get("tool_refs", [])
        for tool in tool_names:
            add(f"tool:{tool}", "tool", str(tool), {"name": tool})
            edges.append({"source": f"agent:{aid}", "target": f"tool:{tool}", "label": "uses"})
        for nxt in item.get("next", []):
            edges.append({"source": f"task:{tid}", "target": f"task:{nxt}", "label": "next"})

    return {"process": process.get("process", "sequential"), "nodes": nodes, "edges": edges}
