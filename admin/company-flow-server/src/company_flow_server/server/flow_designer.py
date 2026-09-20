from __future__ import annotations

import re
from typing import Any

from .flow_models import FlowDefinition, FlowStep
from .registry import CrewRegistry


_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def validate_flow_payload(raw: dict[str, Any], registry: CrewRegistry) -> list[str]:
    errors: list[str] = []
    flow_id = str(raw.get("flow_id", "")).strip()
    if not flow_id or not _ID_RE.match(flow_id):
        errors.append("flow_id must contain only letters, numbers, dot, underscore, or hyphen")
    if not str(raw.get("version", "")).strip():
        errors.append("version is required")
    steps = raw.get("steps")
    if not isinstance(steps, list) or not steps:
        errors.append("at least one step is required")
        return errors

    seen: set[str] = set()
    for idx, step in enumerate(steps):
        sid = str(step.get("step_id", "")).strip()
        if not sid or not _ID_RE.match(sid):
            errors.append(f"steps[{idx}].step_id is invalid")
        if sid in seen:
            errors.append(f"duplicate step_id: {sid}")
        seen.add(sid)
        crew_id, version = step.get("crew_id"), step.get("version")
        try:
            registry.resolve(str(crew_id), str(version))
        except KeyError:
            errors.append(f"crew not deployed: {crew_id}@{version}")
        inputs = step.get("inputs", {})
        if not isinstance(inputs, dict):
            errors.append(f"steps[{idx}].inputs must be an object")
        for ref in _references(inputs):
            if ref.startswith("$steps."):
                parts = ref.split(".")
                if len(parts) < 4 or parts[1] not in seen:
                    errors.append(f"{sid}: reference must target a previous step: {ref}")
    return errors


def build_flow_graph(flow: FlowDefinition, registry: CrewRegistry) -> dict[str, Any]:
    nodes, edges = [], []
    for step in flow.steps:
        manifest = registry.manifest(step.crew_id, step.version)
        nodes.append({
            "id": step.step_id,
            "type": "crew",
            "label": manifest.name,
            "crew_id": step.crew_id,
            "version": step.version,
            "owner": manifest.owner,
            "inputs": step.inputs,
        })
        for ref in _references(step.inputs):
            if ref.startswith("$steps."):
                source = ref.split(".")[1]
                edges.append({"source": source, "target": step.step_id, "label": ref})
    return {
        "flow_id": flow.flow_id,
        "version": flow.version,
        "name": flow.name,
        "description": flow.description,
        "nodes": nodes,
        "edges": edges,
        "output": flow.output,
    }


def payload_to_definition(raw: dict[str, Any]) -> FlowDefinition:
    return FlowDefinition(
        flow_id=raw["flow_id"],
        version=raw["version"],
        name=raw.get("name") or raw["flow_id"],
        description=raw.get("description", ""),
        steps=tuple(
            FlowStep(
                step_id=s["step_id"],
                crew_id=s["crew_id"],
                version=s["version"],
                inputs=dict(s.get("inputs", {})),
                continue_on_error=bool(s.get("continue_on_error", False)),
            )
            for s in raw["steps"]
        ),
        output=dict(raw.get("output", {})),
    )


def _references(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, str) and value.startswith("$"):
        found.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            found.extend(_references(v))
    elif isinstance(value, list):
        for v in value:
            found.extend(_references(v))
    return found


def schema_properties(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if not isinstance(schema, dict):
        return {}
    props = schema.get("properties", {})
    return props if isinstance(props, dict) else {}


def schema_type(field: dict[str, Any]) -> str:
    t = field.get("type")
    if isinstance(t, list):
        t = next((x for x in t if x != "null"), "any")
    return str(t or "any")


def compatibility(source: dict[str, Any], target: dict[str, Any]) -> tuple[bool, int, str]:
    st, tt = schema_type(source), schema_type(target)
    if st == tt:
        return True, 100, "same type"
    if "any" in (st, tt):
        return True, 70, "untyped/any"
    if st == "integer" and tt == "number":
        return True, 90, "integer is compatible with number"
    return False, 0, f"type mismatch: {st} -> {tt}"


def recommend_connections(source_manifest, target_manifest) -> list[dict[str, Any]]:
    src = schema_properties(source_manifest.output_schema)
    dst = schema_properties(target_manifest.input_schema)
    required = set(target_manifest.input_schema.get("required", []))
    recs: list[dict[str, Any]] = []
    for in_name, in_schema in dst.items():
        candidates = []
        for out_name, out_schema in src.items():
            ok, score, reason = compatibility(out_schema, in_schema)
            if not ok:
                continue
            if out_name == in_name:
                score += 50
                reason += ", exact name"
            elif out_name.lower() == in_name.lower():
                score += 40
                reason += ", case-insensitive name"
            candidates.append({
                "source_field": out_name, "target_field": in_name,
                "source_type": schema_type(out_schema), "target_type": schema_type(in_schema),
                "score": score, "reason": reason, "required": in_name in required,
            })
        candidates.sort(key=lambda x: (-x["score"], x["source_field"]))
        if candidates:
            recs.append(candidates[0])
    recs.sort(key=lambda x: (not x["required"], -x["score"], x["target_field"]))
    return recs


def validate_schema_mappings(raw: dict[str, Any], registry: CrewRegistry) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    steps = raw.get("steps", [])
    by_id = {s.get("step_id"): s for s in steps}
    for step in steps:
        target_manifest = registry.manifest(step["crew_id"], step["version"])
        target_props = schema_properties(target_manifest.input_schema)
        required = set(target_manifest.input_schema.get("required", []))
        inputs = step.get("inputs", {})
        for req in sorted(required):
            if req not in inputs:
                issues.append({"level":"error","step_id":step["step_id"],"field":req,"message":"required input is not mapped"})
        for target_field, value in inputs.items():
            if not (isinstance(value, str) and value.startswith("$steps.")):
                continue
            parts=value.split(".")
            if len(parts) < 4 or parts[2] != "outputs":
                continue
            source_step=by_id.get(parts[1])
            source_field=".".join(parts[3:])
            if not source_step:
                continue
            source_manifest=registry.manifest(source_step["crew_id"], source_step["version"])
            source_props=schema_properties(source_manifest.output_schema)
            if source_field not in source_props:
                issues.append({"level":"error","step_id":step["step_id"],"field":target_field,"message":f"source output not found: {source_field}"})
                continue
            if target_field not in target_props:
                issues.append({"level":"warning","step_id":step["step_id"],"field":target_field,"message":"target field is not declared in input_schema"})
                continue
            ok, _, reason=compatibility(source_props[source_field], target_props[target_field])
            if not ok:
                issues.append({"level":"error","step_id":step["step_id"],"field":target_field,"message":reason})
    return issues
