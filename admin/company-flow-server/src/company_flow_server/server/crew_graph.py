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
    edge_seen: set[tuple[str, str, str]] = set()

    def add_node(node_id: str, node_type: str, label: str, detail: dict[str, Any]) -> None:
        if node_id not in seen:
            nodes.append({"id": node_id, "type": node_type, "label": label, "detail": detail})
            seen.add(node_id)

    def add_edge(src_id: str, tgt_id: str, label: str) -> None:
        key = (src_id, tgt_id, label)
        if key not in edge_seen:
            edges.append({"source": src_id, "target": tgt_id, "label": label})
            edge_seen.add(key)

    process_tasks = process.get("tasks", [])
    task_items = list(process_tasks)
    listed_tids = {str(item["id"]) for item in process_tasks if "id" in item}
    for tid, tcfg in tasks.items():
        if tid not in listed_tids:
            task_items.append({"id": tid, "agent": tcfg.get("agent", "")})

    has_task_next_edge = False

    for item in task_items:
        tid = str(item["id"])
        tcfg = tasks.get(tid, {})
        aid = str(item.get("agent") or tcfg.get("agent") or "agent")

        add_node(f"task:{tid}", "task", tid, tcfg)

        if aid:
            acfg = agents.get(aid, {})
            add_node(f"agent:{aid}", "agent", acfg.get("role", aid), {"id": aid, **acfg})
            add_edge(f"task:{tid}", f"agent:{aid}", "assigned")

            tool_names = item.get("tools") or acfg.get("tool_refs", [])
            for tool in tool_names:
                add_node(f"tool:{tool}", "tool", str(tool), {"name": tool})
                add_edge(f"agent:{aid}", f"tool:{tool}", "uses")

        # Check explicit next in process item
        for nxt in item.get("next", []):
            add_edge(f"task:{tid}", f"task:{nxt}", "next")
            has_task_next_edge = True

        # Check context in task definition (context contains preceding task IDs)
        context_list = item.get("context") or tcfg.get("context", [])
        for prev_tid in context_list:
            add_edge(f"task:{prev_tid}", f"task:{tid}", "next")
            has_task_next_edge = True

    # Fallback for sequential process if no next/context edges were defined
    if not has_task_next_edge and len(task_items) > 1 and process.get("process", "sequential") == "sequential":
        for i in range(len(task_items) - 1):
            t1 = str(task_items[i]["id"])
            t2 = str(task_items[i + 1]["id"])
            add_edge(f"task:{t1}", f"task:{t2}", "next")

    return {"process": process.get("process", "sequential"), "nodes": nodes, "edges": edges}
