from __future__ import annotations

from pydantic import ValidationError

from mcp_gateway.domain.errors import ErrorCode, GatewayError
from mcp_gateway.domain.models import McpServerInstance


def parse_instance(raw: dict) -> McpServerInstance:
    try:
        return McpServerInstance.model_validate(raw)
    except ValidationError as exc:
        raise GatewayError(
            ErrorCode.METADATA_INVALID,
            f"Invalid MCP server metadata: {exc.errors()}",
        ) from exc
