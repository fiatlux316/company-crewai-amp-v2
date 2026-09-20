from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True, slots=True)
class Settings:
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    llm_timeout_seconds: float = 30.0
    environment: str = "dev"
    internal_search_base_url: str = "http://internal-search:9000"

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm_base_url=os.environ.get("COMPANY_LLM_BASE_URL", ""),
            llm_api_key=os.environ.get("COMPANY_LLM_API_KEY", ""),
            llm_model=os.environ.get("COMPANY_LLM_MODEL", ""),
            llm_timeout_seconds=float(os.environ.get("COMPANY_LLM_TIMEOUT_SECONDS", "30")),
            environment=os.environ.get("COMPANY_ENV", "dev"),
            internal_search_base_url=os.environ.get("INTERNAL_SEARCH_BASE_URL", ""),
        )
