from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from mcp_gateway.config.gateway_config import McpClientConfig
from mcp_gateway.domain.errors import ErrorCode, GatewayError
from mcp_gateway.domain.models import ToolRoute


class StreamableHttpMcpClient:
    """Minimal Streamable HTTP MCP client adapter.

    The MVP sends a JSON-RPC tools/call request to the selected instance endpoint.
    This keeps the gateway boundary ready for real MCP servers without pulling in
    the official SDK yet.
    """

    def __init__(self, config: McpClientConfig) -> None:
        self._config = config

    def call_tool(self, route: ToolRoute, arguments: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": f"gw-{uuid4().hex}",
            "method": "tools/call",
            "params": {
                "name": route.tool_name,
                "arguments": arguments,
            },
        }
        request = Request(
            route.selected_instance.base_url,
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self._config.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except TimeoutError as exc:
            raise GatewayError(
                ErrorCode.TOOL_DOWNSTREAM_TIMEOUT,
                f"MCP server timed out: {route.selected_instance.instance_id}",
                504,
            ) from exc
        except URLError as exc:
            raise GatewayError(
                ErrorCode.TOOL_EXECUTION_FAILED,
                f"MCP server call failed: {exc.reason}",
                502,
            ) from exc

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            raise GatewayError(
                ErrorCode.TOOL_EXECUTION_FAILED,
                "MCP server returned non-JSON response",
                502,
            ) from exc

        if "error" in payload:
            message = payload["error"].get("message", "MCP server returned error")
            raise GatewayError(ErrorCode.TOOL_EXECUTION_FAILED, message, 502)

        result = payload.get("result")
        if isinstance(result, dict):
            return result
        return {"result": result}
