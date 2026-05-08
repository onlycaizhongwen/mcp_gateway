from __future__ import annotations

from typing import Any

from mcp_gateway.domain.errors import ErrorCode, GatewayError
from mcp_gateway.examples.sample_schemas import SAMPLE_SCHEMAS


class SchemaRegistry:
    def __init__(self, schemas: dict[str, dict[str, Any]] | None = None) -> None:
        self._schemas = schemas or SAMPLE_SCHEMAS

    def get_schema(self, schema_ref: str) -> dict[str, Any]:
        schema = self._schemas.get(schema_ref)
        if schema is None:
            raise GatewayError(
                ErrorCode.TOOL_VALIDATION_FAILED,
                f"Schema not found: {schema_ref}",
                500,
            )
        return schema

    def validate_required(self, schema_ref: str, arguments: dict[str, Any]) -> None:
        schema = self.get_schema(schema_ref)
        required = schema.get("required", [])
        missing = [name for name in required if name not in arguments or arguments[name] is None]
        if missing:
            raise GatewayError(
                ErrorCode.TOOL_VALIDATION_FAILED,
                f"Missing required argument(s): {', '.join(missing)}",
                400,
            )
