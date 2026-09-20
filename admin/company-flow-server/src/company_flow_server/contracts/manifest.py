from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class CrewManifest:
    schema_version: int
    crew_id: str
    version: str
    name: str
    owner: str
    entrypoint: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    description: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)
    runtime: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "CrewManifest":
        required = {"schema_version", "crew_id", "version", "name", "owner", "entrypoint", "input_schema", "output_schema"}
        missing = sorted(required - raw.keys())
        if missing:
            raise ValueError(f"manifest missing fields: {', '.join(missing)}")
        if raw["schema_version"] != 1:
            raise ValueError(f"unsupported manifest schema_version: {raw['schema_version']}")
        if ":" not in raw["entrypoint"]:
            raise ValueError("entrypoint must be '<module>:<callable>'")
        return cls(
            schema_version=raw["schema_version"], crew_id=str(raw["crew_id"]), version=str(raw["version"]),
            name=str(raw["name"]), owner=str(raw["owner"]), entrypoint=str(raw["entrypoint"]),
            input_schema=dict(raw["input_schema"]), output_schema=dict(raw["output_schema"]),
            description=str(raw.get("description", "")), tags=tuple(raw.get("tags", [])), runtime=dict(raw.get("runtime", {})),
        )

    @classmethod
    def load(cls, path: str | Path) -> "CrewManifest":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
