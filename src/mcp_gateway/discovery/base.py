from __future__ import annotations

from typing import Protocol

from mcp_gateway.domain.models import McpServerInstance


class DiscoveryClient(Protocol):
    def list_instances(self) -> list[McpServerInstance]:
        """Return current MCP server instances."""
