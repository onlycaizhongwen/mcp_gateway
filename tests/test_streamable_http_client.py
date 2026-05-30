from unittest.mock import AsyncMock, Mock, patch

import pytest
from mcp.types import CallToolResult, TextContent

from mcp_gateway.client.streamable_http_client import StreamableHttpMcpClient
from mcp_gateway.config.gateway_config import McpClientConfig
from mcp_gateway.discovery.mock_discovery import MockDiscoveryClient
from mcp_gateway.domain.errors import GatewayError
from mcp_gateway.domain.models import ToolRoute


def make_route() -> ToolRoute:
    instance = MockDiscoveryClient().list_instances()[0]
    return ToolRoute(
        tool_name="knowledge.search",
        version="1.0.0",
        tenant_id="tenant-a",
        selected_instance=instance,
        route_reason="test",
    )


def test_streamable_http_client_uses_official_sdk_result_mapping():
    client = StreamableHttpMcpClient(McpClientConfig(mode="streamable-http"))
    route = make_route()
    sdk_result = CallToolResult(content=[], structuredContent={"ok": True})

    with patch.object(client, "_call_tool_async", new=AsyncMock(return_value=sdk_result)) as call_tool:
        result = client.call_tool(route, {"query": "annual leave policy"})

    assert result == {"ok": True}
    call_tool.assert_awaited_once_with(route, {"query": "annual leave policy"})


def test_streamable_http_client_maps_sdk_error_result():
    client = StreamableHttpMcpClient(McpClientConfig(mode="streamable-http"))
    sdk_result = CallToolResult(
        content=[TextContent(type="text", text="boom")],
        isError=True,
    )

    with patch.object(client, "_call_tool_async", new=AsyncMock(return_value=sdk_result)):
        with pytest.raises(GatewayError) as exc_info:
            client.call_tool(make_route(), {"query": "annual leave policy"})

    assert "boom" in exc_info.value.message


def test_streamable_http_client_initializes_and_calls_sdk_session():
    client = StreamableHttpMcpClient(McpClientConfig(mode="streamable-http", timeout_seconds=3))
    route = make_route()
    sdk_result = CallToolResult(content=[], structuredContent={"ok": True})

    transport_context = AsyncMock()
    transport_context.__aenter__.return_value = ("read", "write", lambda: "session-1")
    transport_context.__aexit__.return_value = None

    session_context = AsyncMock()
    session_context.__aenter__.return_value = session_context
    session_context.__aexit__.return_value = None
    session_context.initialize = AsyncMock()
    session_context.call_tool = AsyncMock(return_value=sdk_result)

    http_client_context = AsyncMock()
    http_client_context.__aenter__.return_value = http_client_context
    http_client_context.__aexit__.return_value = None

    with (
        patch(
            "mcp_gateway.client.streamable_http_client.httpx.AsyncClient",
            return_value=http_client_context,
        ) as async_client,
        patch(
            "mcp_gateway.client.streamable_http_client.streamable_http_client",
            Mock(return_value=transport_context),
        ) as transport,
        patch(
            "mcp_gateway.client.streamable_http_client.ClientSession",
            Mock(return_value=session_context),
        ) as client_session,
    ):
        result = client.call_tool(route, {"query": "annual leave policy"})

    assert result == {"ok": True}
    async_client.assert_called_once()
    transport.assert_called_once_with(route.selected_instance.base_url, http_client=http_client_context)
    client_session.assert_called_once_with("read", "write")
    session_context.initialize.assert_awaited_once()
    session_context.call_tool.assert_awaited_once_with(
        "knowledge.search",
        {"query": "annual leave policy"},
    )
