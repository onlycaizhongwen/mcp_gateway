from __future__ import annotations

from typing import Any

import anyio
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.exceptions import McpError
from mcp.types import CallToolResult, TextContent

from mcp_gateway.config.gateway_config import McpClientConfig
from mcp_gateway.domain.errors import ErrorCode, GatewayError
from mcp_gateway.domain.models import ToolRoute


class StreamableHttpMcpClient:
    """Official Python MCP SDK Streamable HTTP adapter."""

    def __init__(self, config: McpClientConfig) -> None:
        self._config = config

    def call_tool(self, route: ToolRoute, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            result = anyio.run(self._call_tool_async, route, arguments)
        except TimeoutError as exc:
            raise GatewayError(
                ErrorCode.TOOL_DOWNSTREAM_TIMEOUT,
                f"MCP server timed out: {route.selected_instance.instance_id}",
                504,
            ) from exc
        except McpError as exc:
            raise GatewayError(ErrorCode.TOOL_EXECUTION_FAILED, exc.error.message, 502) from exc
        except httpx.TimeoutException as exc:
            raise GatewayError(
                ErrorCode.TOOL_DOWNSTREAM_TIMEOUT,
                f"MCP server timed out: {route.selected_instance.instance_id}",
                504,
            ) from exc
        except httpx.HTTPError as exc:
            raise GatewayError(
                ErrorCode.TOOL_EXECUTION_FAILED,
                f"MCP server call failed: {exc}",
                502,
            ) from exc
        except RuntimeError as exc:
            raise GatewayError(ErrorCode.TOOL_EXECUTION_FAILED, str(exc), 502) from exc

        return self._to_gateway_result(result)

    async def _call_tool_async(self, route: ToolRoute, arguments: dict[str, Any]) -> CallToolResult:
        timeout = httpx.Timeout(self._config.timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as http_client:
            async with streamable_http_client(
                route.selected_instance.base_url,
                http_client=http_client,
            ) as (read_stream, write_stream, _get_session_id):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    return await session.call_tool(route.tool_name, arguments)

    def _to_gateway_result(self, result: CallToolResult) -> dict[str, Any]:
        if result.isError:
            message = self._first_text_content(result) or "MCP server returned error"
            raise GatewayError(ErrorCode.TOOL_EXECUTION_FAILED, message, 502)

        if isinstance(result.structuredContent, dict):
            return result.structuredContent

        dumped = result.model_dump(mode="json", by_alias=True, exclude_none=True)
        return {"result": dumped.get("content", [])}

    @staticmethod
    def _first_text_content(result: CallToolResult) -> str | None:
        for content in result.content:
            if isinstance(content, TextContent):
                return content.text
        return None
