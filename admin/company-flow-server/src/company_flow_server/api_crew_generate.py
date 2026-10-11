import os
import re
import json
from pathlib import Path
import pandas as pd
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from .auth.rbac import Principal, current_principal, require

router = APIRouter()

# Dependency or mock of registry for path resolution, to be used inside app.py
# We will just inject the router into app.py and use the existing registry.

def generate_crew_from_excel(excel_bytes: bytes, excel_name: str, registry_root: Path, owner_id: str):
    import io
    df = pd.read_excel(io.BytesIO(excel_bytes))
    df = df.fillna("")
    
    try:
        from .mcp.registry import get_mcp_catalog
        mcp_catalog = {tool.get("name"): tool for tool in get_mcp_catalog()}
    except Exception:
        mcp_catalog = {}

    mcp_dummy_inputs = {}
    mcp_param_props = {}
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
        custom_tool = str(row.get("custom_tool", "")).strip()
        
        if not task_name or not agent_id:
            continue

        tool_refs = [t.strip() for t in mcp.split(",") if t.strip()] if mcp else []
        if custom_tool:
            for ct in custom_tool.split(","):
                ct = ct.strip()
                if ct and ct not in tool_refs:
                    tool_refs.append(ct)

        # MCP 필수 파라미터 자동 추출 및 task description 보완
        needed_in_desc = []
        for t_ref in tool_refs:
            mcp_meta = mcp_catalog.get(t_ref)
            if mcp_meta:
                input_schema = mcp_meta.get("input_schema", {})
                required_fields = input_schema.get("required", [])
                props = input_schema.get("properties", {})
                for field_name in required_fields:
                    input_placeholders.add(field_name)
                    prop_info = props.get(field_name, {})
                    desc = prop_info.get("description", field_name)
                    if field_name not in mcp_dummy_inputs:
                        mcp_dummy_inputs[field_name] = f"[{t_ref} - {desc}]"
                        mcp_param_props[field_name] = {"type": prop_info.get("type", "string")}
                    if f"{{{field_name}}}" not in task_desc:
                        needed_in_desc.append(f"{field_name}: {{{field_name}}}")

        if needed_in_desc:
            task_desc += "\n\n[도구 필수 파라미터]\n" + "\n".join(f"- {item}" for item in needed_in_desc)
            
        if task_desc:
            found = re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", task_desc)
            input_placeholders.update(found)
        
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
            cleaned_out = task_output_file
            if cleaned_out.startswith("./output/"):
                pass
            elif cleaned_out.startswith("output/"):
                cleaned_out = f"./{cleaned_out}"
            elif cleaned_out.startswith("./"):
                cleaned_out = f"./output/{cleaned_out[2:]}"
            else:
                cleaned_out = f"./output/{cleaned_out}"
            task_entry["output_file"] = cleaned_out

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
        if key in mcp_dummy_inputs:
            inputs_data[key] = mcp_dummy_inputs[key]
            input_properties[key] = mcp_param_props.get(key, {"type": "string"})
        else:
            inputs_data[key] = "값을 설정하세요"
            input_properties[key] = {"type": "string"}

    crew_dir_name = excel_name
    version = "1.0.0"
    base_dir = registry_root / f"{crew_dir_name}" / version
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

    custom_tools_code = '''from __future__ import annotations

from typing import Any
from crewai.tools import tool


@tool("custom_tool_dummy")
def custom_tool_dummy(query: str = "") -> str:
    """
    사용자 정의 커스텀 도구 템플릿입니다.
    이 파일에 새로운 @tool 함수를 추가하거나 로직을 수정하면 별도의 서버 재시작 없이 즉시 반영됩니다.

    Args:
        query: 도구 실행에 필요한 입력 인자
    """
    return f"[Custom Tool Dummy Result] Query received: {query}"
'''
    with open(src_dir / "custom_tools.py", "w", encoding="utf-8") as f:
        f.write(custom_tools_code)
        
    manifest = {
      "schema_version": 1,
      "crew_id": f"{crew_dir_name}",
      "version": version,
      "name": crew_dir_name,
      "description": f"Generated crew from {excel_name}.xlsx",
      "owner": owner_id,
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
        
    import hashlib
    from datetime import datetime, timezone
    digest = hashlib.sha256(excel_bytes).hexdigest()
    deployment_data = {
        "sha256": digest,
        "deployed_at": datetime.now(timezone.utc).isoformat()
    }
    with open(base_dir / "deployment.json", "w", encoding="utf-8") as f:
        json.dump(deployment_data, f, indent=2, ensure_ascii=False)
        
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
    
    # 1. Custom tools 동적 로드 (custom_tools.py 또는 custom_tool.py)
    custom_tool_map = {{}}
    for mod_name in (".custom_tools", ".custom_tool"):
        try:
            import importlib
            mod = importlib.import_module(mod_name, package=__package__)
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if hasattr(attr, "name") and hasattr(attr, "run"):
                    custom_tool_map[attr.name] = attr
        except (ImportError, ValueError):
            pass

    # 2. MCP 툴 목록 (custom_tools에 등록된 툴은 MCP에서 제외)
    mcp_tool_refs = [t for t in all_tool_refs if t not in custom_tool_map]

    with runtime.mcp_tools(mcp_tool_refs) as tool_provider:
        tools_list = tool_provider.tools(mcp_tool_refs)
        tool_map = {{t.name: t for t in tools_list}}
        tool_map.update(custom_tool_map)
        
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
                out_file = t_cfg["output_file"]
                for k, v in (inputs or {{}}).items():
                    v_str = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
                    out_file = out_file.replace("{{" + k + "}}", v_str)
                task_kwargs["output_file"] = out_file

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
        "metadata": {{"crew": "{excel_name}", "version": "1.0.0"}},
    }}
"""
    # Fix the regex bug in the generated entrypoint as well
    entrypoint_code = entrypoint_code.replace('r"/\\\\*.*?\\\\*/"', 'r"/\\*.*?\\*/"')
    
    with open(src_dir / "entrypoint.py", "w", encoding="utf-8") as f:
        f.write(entrypoint_code)
        
    return f"{crew_dir_name}", version


@router.post("/api/v1/crews/generate")
async def api_generate_crew(
    file: UploadFile = File(...),
    owner_id: Optional[str] = Form(None),
    overwrite: bool = Form(False),
    p: Principal = Depends(current_principal)
):
    # We will use the FlowRegistry root as the base dir
    # To avoid circular imports, we just know the registry path or import it
    from .app import registry
    
    excel_bytes = await file.read()
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")
    
    excel_name = Path(file.filename).stem
    
    # 동일한 이름의 Crew 폴더가 이미 존재하는지 확인
    crew_target_dir = registry.root / excel_name
    if crew_target_dir.exists() and not overwrite:
        raise HTTPException(
            status_code=409,
            detail="기존에 동일한 이름의 Crew 가 존재합니다."
        )

    # 로그인 사용자 user_id 우선 결정
    effective_owner = p.subject
    if (not effective_owner or effective_owner == "dev-admin") and owner_id:
        effective_owner = owner_id
    elif not effective_owner:
        effective_owner = owner_id or "dev-admin"

    try:
        crew_id, version = generate_crew_from_excel(excel_bytes, excel_name, registry.root, effective_owner)
        return {"status": "success", "crew_id": crew_id, "version": version, "owner": effective_owner}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
