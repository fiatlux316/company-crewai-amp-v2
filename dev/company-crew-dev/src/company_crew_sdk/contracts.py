from __future__ import annotations

from typing import Any


def validate_contract(payload: dict[str, Any], schema: dict[str, Any], *, label: str) -> None:
    """Small dependency-free contract validator for the platform boundary.

    It intentionally validates only required fields and primitive top-level types.
    Production can replace this with full JSON Schema validation without changing
    Crew packages or Flow definitions.
    """

    required = schema.get("required", [])
    missing = [name for name in required if name not in payload]
    if missing:
        raise ValueError(f"{label} missing required fields: {', '.join(missing)}")

    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "object": dict,
        "array": list,
    }
    for name, prop in schema.get("properties", {}).items():
        if name not in payload or "type" not in prop:
            continue
        expected = type_map.get(prop["type"])
        if expected is not None and not isinstance(payload[name], expected):
            raise TypeError(
                f"{label}.{name} expected {prop['type']}, got {type(payload[name]).__name__}"
            )
