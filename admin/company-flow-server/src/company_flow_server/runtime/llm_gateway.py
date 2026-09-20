from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from company_flow_server.bootstrap import build_llm_registry
from company_flow_server.config.settings import Settings

router = APIRouter()


class ChatRequest(BaseModel):
    model: str
    messages: list[dict[str, Any]]
    tools: list[dict[str, Any]] | None = None
    temperature: float | None = None


def _authorize(authorization: str | None) -> None:
    # Replace this demo token check with SSO/OAuth/JWT validation in production.
    from os import getenv
    token = getenv("COMPANY_AGENT_TOKEN")
    if token and authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="invalid runtime token")


@router.post("/v1/chat/completions")
def chat(req: ChatRequest, authorization: str | None = Header(default=None)) -> dict:
    _authorize(authorization)
    settings = Settings.from_env()
    llm = build_llm_registry(settings).get(req.model)
    content = llm.call(req.messages, tools=req.tools, temperature=req.temperature)
    return {
        "id": "company-runtime",
        "object": "chat.completion",
        "model": req.model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
    }
