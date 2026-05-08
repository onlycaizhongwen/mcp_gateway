from __future__ import annotations

from enum import StrEnum


class ErrorCode(StrEnum):
    TOOL_NOT_FOUND = "MCP_TOOL_NOT_FOUND"
    TOOL_DISABLED = "MCP_TOOL_DISABLED"
    TOOL_PERMISSION_DENIED = "MCP_TOOL_PERMISSION_DENIED"
    TOOL_VALIDATION_FAILED = "MCP_TOOL_VALIDATION_FAILED"
    TOOL_IDEMPOTENCY_REQUIRED = "MCP_TOOL_IDEMPOTENCY_REQUIRED"
    TOOL_DOWNSTREAM_TIMEOUT = "MCP_TOOL_DOWNSTREAM_TIMEOUT"
    TOOL_EXECUTION_FAILED = "MCP_TOOL_EXECUTION_FAILED"
    RATE_LIMITED = "MCP_RATE_LIMITED"
    SERVER_UNAVAILABLE = "MCP_SERVER_UNAVAILABLE"
    METADATA_INVALID = "MCP_METADATA_INVALID"


class GatewayError(Exception):
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
