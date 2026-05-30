from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


mcp = FastMCP(
    "Example MCP Server",
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
)


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> Response:
    return JSONResponse({"status": "ok"})


@mcp.tool(name="knowledge.search", structured_output=True)
def knowledge_search(query: str, top_k: int = 3) -> dict[str, Any]:
    return {
        "items": [
            {
                "title": "Local Nacos integration sample knowledge",
                "content": f"Handled by example MCP Server, query={query}",
                "score": 0.99,
            }
        ][:top_k],
        "source": "local-mock-mcp-server",
    }


app = mcp.streamable_http_app()
