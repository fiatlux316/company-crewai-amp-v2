from __future__ import annotations

from typing import Any, Type
import httpx
from pydantic import BaseModel, Field

from .base import CompanyBaseTool


class HttpGetInput(BaseModel):
    path: str = Field(..., description="Allow-listed relative API path")
    query: str | None = Field(None, description="Optional search query")


class InternalSearchTool(CompanyBaseTool):
    name: str = "Internal System Search"
    description: str = "Search an approved internal read-only system API for operational evidence."
    args_schema: Type[BaseModel] = HttpGetInput
    tool_id = "company:internal_search"

    base_url: str
    bearer_token: str = ""
    allowed_prefixes: tuple[str, ...] = ("/search", "/incidents", "/cmdb")

    def execute(self, path: str, query: str | None = None) -> Any:
        if not any(path.startswith(prefix) for prefix in self.allowed_prefixes):
            raise ValueError("path is outside the allow-list")
        headers = {"Authorization": f"Bearer {self.bearer_token}"} if self.bearer_token else {}
        with httpx.Client(base_url=self.base_url, timeout=10.0, headers=headers) as client:
            response = client.get(path, params={"q": query} if query else None)
            response.raise_for_status()
            return response.json()
