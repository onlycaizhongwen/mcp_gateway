import json

from mcp_gateway.config.gateway_config import AuditConfig, AuditFileConfig, GatewayConfig
from mcp_gateway.observability.audit import (
    InMemoryAuditLogger,
    JsonlFileAuditLogger,
    LoggingAuditLogger,
    ToolCallAuditEvent,
    create_audit_logger,
)


def test_in_memory_audit_logger_records_event_without_argument_values():
    logger = InMemoryAuditLogger()

    logger.record_tool_call(
        ToolCallAuditEvent(
            trace_id="trace-1",
            request_id="req-1",
            app_id="app-a",
            tenant_id="tenant-a",
            tool_name="knowledge.search",
            result_code="0",
            duration_ms=12.3,
            argument_keys=["query"],
        )
    )

    assert logger.events[0].argument_keys == ["query"]


def test_jsonl_file_audit_logger_writes_event_without_argument_values(tmp_path):
    audit_file = tmp_path / "audit.jsonl"
    logger = JsonlFileAuditLogger(audit_file)

    logger.record_tool_call(
        ToolCallAuditEvent(
            trace_id="trace-1",
            request_id="req-1",
            app_id="app-a",
            tenant_id="tenant-a",
            tool_name="knowledge.search",
            result_code="0",
            duration_ms=12.3,
            route_instance_id="knowledge-1",
            route_service_name="mcp-server-knowledge",
            argument_keys=["query"],
        )
    )

    line = audit_file.read_text(encoding="utf-8").strip()
    event = json.loads(line)

    assert event["trace_id"] == "trace-1"
    assert event["tool_name"] == "knowledge.search"
    assert event["argument_keys"] == ["query"]
    assert "query" not in event
    assert "created_at" in event


def test_create_audit_logger_uses_file_mode(tmp_path):
    config = GatewayConfig(
        audit=AuditConfig(
            mode="file",
            file=AuditFileConfig(path=str(tmp_path / "audit.jsonl")),
        )
    )

    logger = create_audit_logger(config)

    assert isinstance(logger, JsonlFileAuditLogger)


def test_create_audit_logger_defaults_to_logging():
    logger = create_audit_logger(GatewayConfig())

    assert isinstance(logger, LoggingAuditLogger)
