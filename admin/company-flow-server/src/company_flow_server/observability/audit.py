from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
import logging
from typing import Any


logger = logging.getLogger("company_agent.audit")


@dataclass(slots=True)
class AuditEvent:
    event_type: str
    component: str
    action: str
    status: str
    actor: str = "agent"
    correlation_id: str | None = None
    metadata: dict[str, Any] | None = None
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat()


class AuditLogger:
    def emit(self, event: AuditEvent) -> None:
        # Replace this sink with Kafka/Splunk/OpenTelemetry in production.
        logger.info(json.dumps(asdict(event), ensure_ascii=False, default=str))
