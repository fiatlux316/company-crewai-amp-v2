import sys
import os
import json
from pathlib import Path
import pandas as pd
import math

def is_nan(val):
    if isinstance(val, float) and math.isnan(val):
        return True
    return pd.isna(val)

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run --with pandas --with openpyxl python generate.py <excel_file_name>")
        sys.exit(1)
        
    arg_name = sys.argv[1]
    base_dir = Path(__file__).parent
    excel_path = base_dir / "crew_specs" / arg_name
    
    if not excel_path.exists() and not excel_path.suffix:
        excel_path = excel_path.with_suffix(".xlsx")
        
    if not excel_path.exists():
        print(f"File not found: {excel_path}")
        sys.exit(1)
        
    excel_name = excel_path.stem
    crew_dir_name = f"{excel_name}"
    
    base_dir = Path(__file__).parent / "crew_packages" / crew_dir_name
    src_dir = base_dir / "src" / crew_dir_name
    
    src_dir.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_excel(excel_path)
    
    # Fill nan with empty strings for text columns
    df = df.fillna("")
    
    agents = {}
    tasks = {}
    process_tasks = []
    
    for idx, row in df.iterrows():
        task_name = str(row.get("task_name", "")).strip()
        task_context = str(row.get("task_context", "")).strip()
        task_desc = str(row.get("task_description", "")).strip().replace("\\n", "\n")
        task_expected = str(row.get("task_expected_output", "")).strip().replace("\\n", "\n")
        task_output_file = str(row.get("task_output_file", "")).strip()
        
        agent_id = str(row.get("task_agent", "")).strip()
        agent_role = str(row.get("agent_role", "")).strip().replace("\\n", "\n")
        agent_goal = str(row.get("agent_goal", "")).strip().replace("\\n", "\n")
        agent_backstory = str(row.get("agent_backstory", "")).strip().replace("\\n", "\n")
        agent_llm_ref = str(row.get("agent_llm_ref", "")).strip()
        if not agent_llm_ref:
            agent_llm_ref = "company/devx-llm"
        mcp = str(row.get("mcp", "")).strip()
        
        if not task_name or not agent_id:
            continue
            
        tool_refs = [t.strip() for t in mcp.split(",") if t.strip()] if mcp else []
        
        if agent_id not in agents:
            agents[agent_id] = {
                "role": agent_role,
                "goal": agent_goal,
                "backstory": agent_backstory,
                "llm_ref": agent_llm_ref,
                "tool_refs": tool_refs,
                "settings": {
                    "verbose": True,
                    "allow_delegation": False,
                    "max_iter": 8
                }
            }
        else:
            # If agent already exists, append new tools if any
            for t in tool_refs:
                if t not in agents[agent_id]["tool_refs"]:
                    agents[agent_id]["tool_refs"].append(t)
                    
        # Parse context dependencies
        context_list = [c.strip() for c in task_context.split(",") if c.strip()] if task_context else []
        
        task_entry = {
            "description": task_desc,
            "expected_output": task_expected,
            "context": context_list
        }
        if task_output_file:
            task_entry["output_file"] = task_output_file

        tasks[task_name] = task_entry
        
        process_tasks.append({
            "id": task_name,
            "agent": agent_id,
            "tools": tool_refs,
            "next": []
        })
        
    # Write agents.jsonc
    with open(src_dir / "agents.jsonc", "w", encoding="utf-8") as f:
        json.dump(agents, f, indent=2, ensure_ascii=False)
        
    # Write tasks.jsonc
    with open(src_dir / "tasks.jsonc", "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
        
    # Write process.jsonc
    process_cfg = {
        "process": "sequential",
        "tasks": process_tasks
    }
    with open(src_dir / "process.jsonc", "w", encoding="utf-8") as f:
        json.dump(process_cfg, f, indent=2, ensure_ascii=False)
        
    # Write __init__.py
    with open(src_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write("")
        
    # Write crew-manifest.json
    manifest = {
      "schema_version": 1,
      "crew_id": f"ops.{excel_name}",
      "version": "1.0.0",
      "name": f"{excel_name} Crew",
      "description": f"Generated crew from {excel_name}.xlsx",
      "owner": "SW Engineer",
      "entrypoint": f"{crew_dir_name}.entrypoint:run",
      "input_schema": {
        "type": "object",
        "properties": {}
      },
      "output_schema": {
        "type": "object",
        "properties": {}
      },
      "tags": ["generated"],
      "runtime": {
        "crewai": ">=1.15.17,<1.16"
      },
      "process_definition": f"src/{crew_dir_name}/process.jsonc"
    }
    with open(base_dir / "crew-manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    # Write entrypoint.py
    entrypoint_code = f"""from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from crewai import Agent, Crew, Process, Task

HERE = Path(__file__).parent


def _load_jsonc(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"/\\*.*?\\*/", "", text, flags=re.S)
    text = re.sub(r"(^|\\s)//.*$", r"\\1", text, flags=re.M)
    return json.loads(text)


def run(inputs: dict[str, Any], runtime: Any) -> dict[str, Any]:
    agents_cfg = _load_jsonc(HERE / "agents.jsonc")
    tasks_cfg = _load_jsonc(HERE / "tasks.jsonc")
    process_cfg = _load_jsonc(HERE / "process.jsonc")

    all_tool_refs = set()
    for ag_cfg in agents_cfg.values():
        all_tool_refs.update(ag_cfg.get("tool_refs", []))
    
    with runtime.mcp_tools(list(all_tool_refs)) as tool_provider:
        tools_list = tool_provider.tools(list(all_tool_refs))
        tool_map = {{t.name: t for t in tools_list}}
        
        # Build agents
        agents = {{}}
        for ag_id, cfg in agents_cfg.items():
            ag_tools = [tool_map[t_ref] for t_ref in cfg.get("tool_refs", []) if t_ref in tool_map]
            agents[ag_id] = Agent(
                role=cfg["role"],
                goal=cfg["goal"],
                backstory=cfg["backstory"],
                llm=runtime.get_llm(cfg.get("llm_ref", "company/devx-llm")),
                tools=ag_tools,
                **cfg.get("settings", {{}}),
            )
            
        # Build tasks
        tasks = {{}}
        ordered_tasks = []
        for task_def in process_cfg.get("tasks", []):
            t_id = task_def["id"]
            t_cfg = tasks_cfg[t_id]
            t_agent = agents[task_def["agent"]]
            
            desc = t_cfg["description"]
            # Dynamic template formatting if inputs exist
            try:
                desc = desc.format(**inputs)
            except KeyError:
                pass
                
            task_kwargs = {{
                "description": desc,
                "expected_output": t_cfg["expected_output"],
                "agent": t_agent,
            }}
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
        parsed_result = {{"raw_result": str(result)}}
        
    return {{
        "outputs": parsed_result,
        "metadata": {{"crew": "ops.{excel_name}", "version": "1.0.0"}},
    }}
"""
    with open(src_dir / "entrypoint.py", "w", encoding="utf-8") as f:
        f.write(entrypoint_code)
        
    print(f"Successfully generated Crew package: {crew_dir_name}")

if __name__ == "__main__":
    main()
