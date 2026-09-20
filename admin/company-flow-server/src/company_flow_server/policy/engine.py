from __future__ import annotations

from dataclasses import dataclass, field

from .models import PolicyDecision, RiskLevel, ToolExecutionContext


@dataclass(slots=True)
class ToolPolicy:
    risk_level: RiskLevel = RiskLevel.READ_ONLY
    allowed_environments: set[str] = field(default_factory=lambda: {"dev", "test", "prod"})
    requires_change_ticket_in_prod: bool = False


class PolicyEngine:
    """Fail-closed policy gate. Keep authorization outside the LLM."""

    def __init__(self, policies: dict[str, ToolPolicy] | None = None) -> None:
        self._policies = policies or {}

    def evaluate(self, tool_id: str, ctx: ToolExecutionContext) -> PolicyDecision:
        policy = self._policies.get(tool_id, ToolPolicy())
        if ctx.environment not in policy.allowed_environments:
            return PolicyDecision(
                allowed=False,
                reason=f"tool {tool_id} is not allowed in {ctx.environment}",
                risk_level=policy.risk_level,
            )

        requires_approval = policy.risk_level >= RiskLevel.MEDIUM
        if policy.requires_change_ticket_in_prod and ctx.environment == "prod" and not ctx.change_ticket:
            return PolicyDecision(
                allowed=False,
                reason="production execution requires a change ticket",
                risk_level=policy.risk_level,
                required_controls=["change_ticket"],
            )

        if requires_approval and not ctx.approved:
            return PolicyDecision(
                allowed=False,
                requires_approval=True,
                reason="human approval required",
                risk_level=policy.risk_level,
                required_controls=["human_approval"],
            )

        return PolicyDecision(
            allowed=True,
            requires_approval=requires_approval,
            reason="policy checks passed",
            risk_level=policy.risk_level,
        )
