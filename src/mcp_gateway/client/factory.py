from __future__ import annotations

from mcp_gateway.client.base import McpClient
from mcp_gateway.client.mock_mcp_client import MockMcpClient
from mcp_gateway.client.streamable_http_client import StreamableHttpMcpClient
from mcp_gateway.config.gateway_config import GatewayConfig


def create_mcp_client(config: GatewayConfig) -> McpClient:
    if config.mcp_client.mode == "streamable-http":
        return StreamableHttpMcpClient(config.mcp_client)
    return MockMcpClient()
