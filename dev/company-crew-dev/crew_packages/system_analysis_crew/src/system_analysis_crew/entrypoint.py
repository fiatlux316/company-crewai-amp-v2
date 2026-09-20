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
    cfg = agents_cfg["system_issue_analyst"]

    # Local developers discover tools remotely from the administrator-owned MCP server.
    # On the team server the runtime object uses the same method contract but may bind
    # directly to internal tools. Crew source stays identical in both environments.
    with runtime.mcp_tools(cfg["tool_refs"]) as tool_provider:
        tools = tool_provider.tools(cfg["tool_refs"])
        analyst = Agent(
            role=cfg["role"],
            goal=cfg["goal"],
            backstory=cfg["backstory"],
            llm=runtime.get_llm(cfg["llm_ref"]),
            tools=tools,
            **cfg.get("settings", {}),
        )
        task_cfg = tasks_cfg["triage"]
        task = Task(
            description=task_cfg["description"].format(
                query=inputs["query"],
                time_range=inputs["time_range"],
                limit=inputs["limit"],
            ),
            expected_output=task_cfg["expected_output"] + "\n반드시 다음 JSON 키를 포함해서 출력하세요: service, resource, status, error_message, start_time, duration",
            agent=analyst,
        )
        result = Crew(agents=[analyst], tasks=[task], process=Process.sequential, verbose=True).kickoff()

    # 결과 문자열에서 JSON 파싱 (마크다운 코드블록 제거)
    raw_text = str(result).strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:]
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3]
    
    try:
        parsed_result = json.loads(raw_text.strip())
        print("parsed_result: ", parsed_result)
    except Exception:
        # JSON 파싱 실패 시 폴백
        parsed_result = {
            "service": "Unknown",
            "resource": "Unknown",
            "status": "Error",
            "error_message": str(result),
            "start_time": "Unknown",
            "duration": "Unknown"
        }

    return {
        "outputs": {
            "service": parsed_result.get("service", "Unknown"),
            "resource": parsed_result.get("resource", "Unknown"),
            "status": parsed_result.get("status", "Unknown"),
            "error_message": parsed_result.get("error_message", ""),
            "start_time": parsed_result.get("start_time", "Unknown"),
            "duration": parsed_result.get("duration", "Unknown")
        },
        "metadata": {"crew": "ops.system-issue-analysis", "version": "1.0.0"},
    }
