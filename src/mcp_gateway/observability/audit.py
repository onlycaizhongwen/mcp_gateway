from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolCallAuditEvent:
    trace_id: str
    request_id: str
    app_id: str | None
    tenant_id: str | None
    tool_name: str
    result_code: str
    duration_ms: float
    route_instance_id: str | None = None
    route_service_name: str | None = None
    argument_keys: list[str] = field(default_factory=list)


class AuditLogger(Protocol):
    def record_tool_call(self, event: ToolCallAuditEvent) -> None:
        """Record a tool call audit event."""


class LoggingAuditLogger:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("mcp_gateway.audit")

    def record_tool_call(self, event: ToolCallAuditEvent) -> None:
        self._logger.info(
            "tool_call trace_id=%s request_id=%s app_id=%s tenant_id=%s "
            "tool_name=%s result_code=%s duration_ms=%.2f route_instance_id=%s "
            "route_service_name=%s argument_keys=%s",
            event.trace_id,
            event.request_id,
            event.app_id,
            event.tenant_id,
            event.tool_name,
            event.result_code,
            event.duration_ms,
            event.route_instance_id,
            event.route_service_name,
            event.argument_keys,
        )


class InMemoryAuditLogger:
    def __init__(self) -> None:
        self.events: list[ToolCallAuditEvent] = []

    def record_tool_call(self, event: ToolCallAuditEvent) -> None:
        self.events.append(event)
