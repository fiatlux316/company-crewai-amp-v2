from __future__ import annotations

import json
from typing import Any
from pydantic import BaseModel, Field


class ToolEnvelope(BaseModel):
    ok: bool
    data: Any = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def as_llm_text(self) -> str:
        # Return a string deliberately: this avoids framework-specific nested-dict parsing issues.
        return json.dumps(self.model_dump(mode="json"), ensure_ascii=False, default=str)
