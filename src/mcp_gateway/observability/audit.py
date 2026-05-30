from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from mcp_gateway.config.gateway_config import GatewayConfig


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


class JsonlFileAuditLogger:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def record_tool_call(self, event: ToolCallAuditEvent) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "trace_id": event.trace_id,
            "request_id": event.request_id,
            "app_id": event.app_id,
            "tenant_id": event.tenant_id,
            "tool_name": event.tool_name,
            "result_code": event.result_code,
            "duration_ms": event.duration_ms,
            "route_instance_id": event.route_instance_id,
            "route_service_name": event.route_service_name,
            "argument_keys": event.argument_keys,
        }
        with self._path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def create_audit_logger(config: GatewayConfig) -> AuditLogger:
    if config.audit.mode == "file":
        return JsonlFileAuditLogger(config.audit.file.path)
    return LoggingAuditLogger()
