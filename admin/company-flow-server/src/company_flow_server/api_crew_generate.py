import os
import re
import json
from pathlib import Path
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from .auth.rbac import Principal, require

router = APIRouter()

# Dependency or mock of registry for path resolution, to be used inside app.py
# We will just inject the router into app.py and use the existing registry.

def generate_crew_from_excel(excel_bytes: bytes, excel_name: str, registry_root: Path):
    import io
    df = pd.read_excel(io.BytesIO(excel_bytes))
    df = df.fillna("")
    
    agents = {}
    tasks = {}
    process_tasks = []
    input_placeholders = set()
    
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
            
        if task_desc:
            found = re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", task_desc)
            input_placeholders.update(found)

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
            for t in tool_refs:
                if t not in agents[agent_id]["tool_refs"]:
                    agents[agent_id]["tool_refs"].append(t)
                    
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

    inputs_data = {}
    input_properties = {}
    for key in sorted(input_placeholders):
        inputs_data[key] = "값을 설정하세요"
        input_properties[key] = {"type": "string"}

    crew_dir_name = excel_name
    version = "1.0.0"
    base_dir = registry_root / f"ops.{crew_dir_name}" / version
    src_dir = base_dir / "src" / crew_dir_name
    
    src_dir.mkdir(parents=True, exist_ok=True)
    
    with open(src_dir / "inputs.json", "w", encoding="utf-8") as f:
        json.dump(inputs_data, f, indent=2, ensure_ascii=False)

    with open(src_dir / "agents.jsonc", "w", encoding="utf-8") as f:
        json.dump(agents, f, indent=2, ensure_ascii=False)
        
    with open(src_dir / "tasks.jsonc", "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2, ensure_ascii=False)
        
    process_cfg = {
        "process": "sequential",
        "tasks": process_tasks
    }
    with open(src_dir / "process.jsonc", "w", encoding="utf-8") as f:
        json.dump(process_cfg, f, indent=2, ensure_ascii=False)
        
    with open(src_dir / "__init__.py", "w", encoding="utf-8") as f:
        f.write("")
        
    manifest = {
      "schema_version": 1,
      "crew_id": f"ops.{crew_dir_name}",
      "version": version,
      "name": f"{crew_dir_name} Crew",
      "description": f"Generated crew from {excel_name}.xlsx",
      "owner": "SW Engineer",
      "entrypoint": f"{crew_dir_name}.entrypoint:run",
      "input_schema": {
        "type": "object",
        "properties": input_properties
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
        
    entrypoint_code = f"""from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from crewai import Agent, Crew, Process, Task

HERE = Path(__file__).parent


def _load_jsonc(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
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
            expected = t_cfg["expected_output"]
            for k, v in (inputs or {{}}).items():
                v_str = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
                desc = desc.replace("{{" + k + "}}", v_str)
                expected = expected.replace("{{" + k + "}}", v_str)
                
            task_kwargs = {{
                "description": desc,
                "expected_output": expected,
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
    # Fix the regex bug in the generated entrypoint as well
    entrypoint_code = entrypoint_code.replace('r"/\\\\*.*?\\\\*/"', 'r"/\\*.*?\\*/"')
    
    with open(src_dir / "entrypoint.py", "w", encoding="utf-8") as f:
        f.write(entrypoint_code)
        
    return f"ops.{crew_dir_name}", version


@router.post("/api/v1/crews/generate")
async def api_generate_crew(file: UploadFile = File(...)):
    # We will use the FlowRegistry root as the base dir
    # To avoid circular imports, we just know the registry path or import it
    from .app import registry
    
    excel_bytes = await file.read()
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
    
    excel_name = Path(file.filename).stem
    
    try:
        crew_id, version = generate_crew_from_excel(excel_bytes, excel_name, registry.root)
        return {"status": "success", "crew_id": crew_id, "version": version}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
