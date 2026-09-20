from __future__ import annotations

from abc import abstractmethod
from typing import Any, ClassVar

from crewai.tools import BaseTool

from company_flow_server.observability.audit import AuditEvent, AuditLogger
from company_flow_server.policy.engine import PolicyEngine
from company_flow_server.policy.models import ToolExecutionContext
from .envelope import ToolEnvelope


class CompanyBaseTool(BaseTool):
    """Enterprise tool boundary: policy -> execution -> normalized output -> audit."""

    tool_id: ClassVar[str] = "company:base"
    policy_engine: PolicyEngine
    audit_logger: AuditLogger
    execution_context: ToolExecutionContext

    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        *,
        policy_engine: PolicyEngine,
        execution_context: ToolExecutionContext | None = None,
        audit_logger: AuditLogger | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            policy_engine=policy_engine,
            execution_context=execution_context or ToolExecutionContext(),
            audit_logger=audit_logger or AuditLogger(),
            **kwargs,
        )

    def _run(self, **kwargs: Any) -> str:
        decision = self.policy_engine.evaluate(self.tool_id, self.execution_context)
        self.audit_logger.emit(
            AuditEvent(
                event_type="tool.policy",
                component=self.tool_id,
                action="evaluate",
                status="allow" if decision.allowed else "deny",
                correlation_id=self.execution_context.correlation_id,
                metadata=decision.model_dump(mode="json"),
            )
        )
        if not decision.allowed:
            return ToolEnvelope(ok=False, error=decision.reason).as_llm_text()

        try:
            data = self.execute(**kwargs)
            self.audit_logger.emit(
                AuditEvent(
                    event_type="tool.execute",
                    component=self.tool_id,
                    action=self.name,
                    status="success",
                    correlation_id=self.execution_context.correlation_id,
                )
            )
            return ToolEnvelope(ok=True, data=data).as_llm_text()
        except Exception as exc:  # normalize provider/tool errors at the boundary
            self.audit_logger.emit(
                AuditEvent(
                    event_type="tool.execute",
                    component=self.tool_id,
                    action=self.name,
                    status="error",
                    correlation_id=self.execution_context.correlation_id,
                    metadata={"error_type": type(exc).__name__},
                )
            )
            return ToolEnvelope(ok=False, error=f"{type(exc).__name__}: {exc}").as_llm_text()

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        raise NotImplementedError
