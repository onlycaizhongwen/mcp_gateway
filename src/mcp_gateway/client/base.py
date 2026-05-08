from __future__ import annotations

from typing import Any, Protocol

from mcp_gateway.domain.models import ToolRoute


class McpClient(Protocol):
    def call_tool(self, route: ToolRoute, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call selected MCP server tool."""
