from __future__ import annotations

from enum import IntEnum
from pydantic import BaseModel, Field


class RiskLevel(IntEnum):
    READ_ONLY = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ToolExecutionContext(BaseModel):
    user_id: str = "agent"
    environment: str = "dev"
    correlation_id: str | None = None
    approved: bool = False
    change_ticket: str | None = None


class PolicyDecision(BaseModel):
    allowed: bool
    requires_approval: bool = False
    reason: str
    risk_level: RiskLevel
    required_controls: list[str] = Field(default_factory=list)
