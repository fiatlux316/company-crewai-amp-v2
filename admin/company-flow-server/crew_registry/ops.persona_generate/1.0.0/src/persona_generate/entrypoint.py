from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from crewai import Agent, Crew, Process, Task

HERE = Path(__file__).parent


def _load_jsonc(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"(^|\s)//.*$", r"\1", text, flags=re.M)
    return json.loads(text)


def run(inputs: dict[str, Any], runtime: Any) -> dict[str, Any]:
    agents_cfg = _load_jsonc(HERE / "agents.jsonc")
    tasks_cfg = _load_jsonc(HERE / "tasks.jsonc")
    process_cfg = _load_jsonc(HERE / "process.jsonc")

    all_tool_refs = set()
    for ag_cfg in agents_cfg.values():
        all_tool_refs.update(ag_cfg.get("tool_refs", []))
        
    mcp_tool_refs = {ref for ref in all_tool_refs if ref not in ["markdown_to_excel_converter"]}
    
    with runtime.mcp_tools(list(mcp_tool_refs)) as tool_provider:
        tools_list = tool_provider.tools(list(mcp_tool_refs))
        tool_map = {t.name: t for t in tools_list}
        
        # Inject custom tools
        try:
            from .custom_tools import markdown_to_excel_tool
            tool_map["markdown_to_excel_converter"] = markdown_to_excel_tool
        except ImportError:
            pass
        
        # Build agents
        agents = {}
        for ag_id, cfg in agents_cfg.items():
            ag_tools = [tool_map[t_ref] for t_ref in cfg.get("tool_refs", []) if t_ref in tool_map]
            agents[ag_id] = Agent(
                role=cfg["role"],
                goal=cfg["goal"],
                backstory=cfg["backstory"],
                llm=runtime.get_llm(cfg.get("llm_ref", "company/devx-llm")),
                tools=ag_tools,
                **cfg.get("settings", {}),
            )
            
        # Build tasks
        tasks = {}
        ordered_tasks = []
        for task_def in process_cfg.get("tasks", []):
            t_id = task_def["id"]
            t_cfg = tasks_cfg[t_id]
            t_agent = agents[task_def["agent"]]
            
            desc = t_cfg["description"]
            expected = t_cfg["expected_output"]
            for k, v in (inputs or {}).items():
                v_str = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
                desc = desc.replace("{" + k + "}", v_str)
                expected = expected.replace("{" + k + "}", v_str)
                
            task_kwargs = {
                "description": desc,
                "expected_output": expected,
                "agent": t_agent,
            }
            if "output_file" in t_cfg and t_cfg["output_file"]:
                task_kwargs["output_file"] = t_cfg["output_file"]

            task_obj = Task(**task_kwargs)
            tasks[t_id] = task_obj
            ordered_tasks.append(task_obj)
            
        # Resolve context dependencies (task_context)
        for t_id, task_obj in tasks.items():
            ctx_ids = tasks_cfg[t_id].get("context", [])
            if ctx_ids:
                task_obj.context = [tasks[cid] for cid in ctx_ids if cid in tasks]
                
        crew_process = Process.sequential
        result = Crew(agents=list(agents.values()), tasks=ordered_tasks, process=crew_process, verbose=True).kickoff()
        
    raw_text = str(result).strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    
    try:
        parsed_result = json.loads(raw_text.strip())
    except Exception:
        parsed_result = {"raw_result": str(result)}
        
    return {
        "outputs": parsed_result,
        "metadata": {"crew": "ops.persona_generate", "version": "1.0.0"},
    }
