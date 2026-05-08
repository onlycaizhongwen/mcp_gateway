from __future__ import annotations

from collections import defaultdict

from mcp_gateway.catalog.tool_catalog import ToolCatalog
from mcp_gateway.domain.errors import ErrorCode, GatewayError
from mcp_gateway.domain.models import ToolRoute
from mcp_gateway.routing.circuit_breaker import CircuitBreaker


class RouterScheduler:
    def __init__(self, catalog: ToolCatalog, circuit_breaker: CircuitBreaker | None = None) -> None:
        self._catalog = catalog
        self._circuit_breaker = circuit_breaker
        self._cursors: dict[str, int] = defaultdict(int)

    def select_route(
        self,
        tool_name: str,
        tenant_id: str | None = None,
        version: str | None = None,
    ) -> ToolRoute:
        tool = self._catalog.get_tool(tool_name, version)
        if tool is None:
            raise GatewayError(ErrorCode.TOOL_NOT_FOUND, f"Tool not found: {tool_name}", 404)
        if not tool.enabled:
            raise GatewayError(ErrorCode.TOOL_DISABLED, f"Tool disabled: {tool_name}", 409)
        if not tool.provider_instances:
            raise GatewayError(
                ErrorCode.SERVER_UNAVAILABLE,
                f"No healthy MCP server instance for tool: {tool_name}",
                503,
            )

        candidates = [
            instance
            for instance in tool.provider_instances
            if self._circuit_breaker is None or self._circuit_breaker.can_call(instance.instance_id)
        ]
        if not candidates:
            raise GatewayError(
                ErrorCode.SERVER_UNAVAILABLE,
                f"All MCP server instances are unavailable for tool: {tool_name}",
                503,
            )

        cursor_key = f"{tool.name}:{tool.version}"
        index = self._cursors[cursor_key] % len(candidates)
        self._cursors[cursor_key] += 1
        instance = candidates[index]

        return ToolRoute(
            tool_name=tool.name,
            version=tool.version,
            tenant_id=tenant_id,
            selected_instance=instance,
            route_reason="round-robin healthy instance with circuit breaker filter",
        )
