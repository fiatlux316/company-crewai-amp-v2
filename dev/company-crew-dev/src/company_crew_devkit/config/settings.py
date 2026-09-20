from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class Settings:
    runtime_url: str
    mcp_url: str
    access_token: str
    environment: str = "dev"
    llm_timeout_seconds: float = 60.0

    @classmethod
    def from_env(cls) -> "Settings":
        runtime_url = os.environ.get("COMPANY_RUNTIME_URL", "http://localhost:8080")
        return cls(
            runtime_url=runtime_url.rstrip("/"),
            mcp_url=os.environ.get("COMPANY_MCP_URL", f"{runtime_url.rstrip('/')}/mcp"),
            access_token=os.environ.get("COMPANY_AGENT_TOKEN", ""),
            environment=os.environ.get("COMPANY_ENV", "dev"),
            llm_timeout_seconds=float(os.environ.get("COMPANY_LLM_TIMEOUT_SECONDS", "60")),
        )
