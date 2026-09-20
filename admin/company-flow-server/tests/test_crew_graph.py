from pathlib import Path
import json
from company_flow_server.server.crew_graph import build_crew_graph


def test_graph_builds_task_agent_tool(tmp_path: Path):
    (tmp_path/'src'/'x').mkdir(parents=True)
    (tmp_path/'crew-manifest.json').write_text(json.dumps({'process_definition':'src/x/process.jsonc'}))
    (tmp_path/'src'/'x'/'process.jsonc').write_text('{"process":"sequential","tasks":[{"id":"t","agent":"a","tools":["tool.x"],"next":[]}]}')
    (tmp_path/'src'/'x'/'agents.jsonc').write_text('{"a":{"role":"Analyst","tool_refs":["tool.x"]}}')
    (tmp_path/'src'/'x'/'tasks.jsonc').write_text('{"t":{"description":"do it"}}')
    graph=build_crew_graph(tmp_path)
    assert {n['type'] for n in graph['nodes']} == {'task','agent','tool'}
    assert len(graph['edges']) == 2
