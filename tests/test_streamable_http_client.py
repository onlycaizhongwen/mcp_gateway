import json
from unittest.mock import patch

import pytest

from mcp_gateway.client.streamable_http_client import StreamableHttpMcpClient
from mcp_gateway.config.gateway_config import McpClientConfig
from mcp_gateway.discovery.mock_discovery import MockDiscoveryClient
from mcp_gateway.domain.errors import GatewayError
from mcp_gateway.domain.models import ToolRoute


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def make_route() -> ToolRoute:
    instance = MockDiscoveryClient().list_instances()[0]
    return ToolRoute(
        tool_name="knowledge.search",
        version="1.0.0",
        tenant_id="tenant-a",
        selected_instance=instance,
        route_reason="test",
    )


def test_streamable_http_client_sends_tools_call():
    client = StreamableHttpMcpClient(McpClientConfig(mode="streamable-http"))
    route = make_route()

    with patch("mcp_gateway.client.streamable_http_client.urlopen") as urlopen:
        urlopen.return_value = FakeResponse({"jsonrpc": "2.0", "id": "1", "result": {"ok": True}})

        result = client.call_tool(route, {"query": "年假政策"})

    assert result == {"ok": True}
    request = urlopen.call_args.args[0]
    body = json.loads(request.data.decode("utf-8"))
    assert body["method"] == "tools/call"
    assert body["params"]["name"] == "knowledge.search"


def test_streamable_http_client_maps_mcp_error():
    client = StreamableHttpMcpClient(McpClientConfig(mode="streamable-http"))

    with patch("mcp_gateway.client.streamable_http_client.urlopen") as urlopen:
        urlopen.return_value = FakeResponse(
            {"jsonrpc": "2.0", "id": "1", "error": {"code": -32000, "message": "boom"}}
        )

        with pytest.raises(GatewayError):
            client.call_tool(make_route(), {"query": "年假政策"})
