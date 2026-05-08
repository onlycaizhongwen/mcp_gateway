from mcp_gateway.observability.audit import InMemoryAuditLogger, ToolCallAuditEvent


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
