from __future__ import annotations

from typing import Any

from mcp_gateway.domain.errors import ErrorCode, GatewayError
from mcp_gateway.domain.models import ToolRoute


class MockMcpClient:
    def call_tool(self, route: ToolRoute, arguments: dict[str, Any]) -> dict[str, Any]:
        if route.tool_name == "knowledge.search":
            return self._knowledge_search(route, arguments)
        if route.tool_name == "approval.create_task":
            return self._approval_create_task(route, arguments)
        if route.tool_name == "document.generate":
            return self._document_generate(route, arguments)

        raise GatewayError(
            ErrorCode.TOOL_EXECUTION_FAILED,
            f"Mock client does not implement {route.tool_name}",
            500,
        )

    def _knowledge_search(self, route: ToolRoute, arguments: dict[str, Any]) -> dict[str, Any]:
        query = arguments.get("query")
        if not query:
            raise GatewayError(ErrorCode.TOOL_VALIDATION_FAILED, "Missing required argument: query")

        top_k = arguments.get("top_k", 3)
        return {
            "answer": f"Mock answer for: {query}",
            "references": [
                {
                    "title": "员工手册",
                    "source": "mock://knowledge/employee-handbook",
                    "score": 0.91,
                }
            ][:top_k],
            "route": {
                "instanceId": route.selected_instance.instance_id,
                "serviceName": route.selected_instance.service_name,
                "reason": route.route_reason,
            },
        }

    def _approval_create_task(self, route: ToolRoute, arguments: dict[str, Any]) -> dict[str, Any]:
        title = arguments.get("title")
        applicant = arguments.get("applicant")
        approver = arguments.get("approver")
        if not title or not applicant or not approver:
            raise GatewayError(
                ErrorCode.TOOL_VALIDATION_FAILED,
                "Missing required argument: title, applicant or approver",
            )

        return {
            "taskId": "mock-approval-001",
            "status": "created",
            "approvalUrl": "mock://approval/tasks/mock-approval-001",
            "route": {
                "instanceId": route.selected_instance.instance_id,
                "serviceName": route.selected_instance.service_name,
                "reason": route.route_reason,
            },
        }

    def _document_generate(self, route: ToolRoute, arguments: dict[str, Any]) -> dict[str, Any]:
        template = arguments.get("template")
        title = arguments.get("title")
        if not template or not title:
            raise GatewayError(
                ErrorCode.TOOL_VALIDATION_FAILED,
                "Missing required argument: template or title",
            )

        output_format = arguments.get("format", "markdown")
        return {
            "documentId": "mock-document-001",
            "title": title,
            "format": output_format,
            "content": f"# {title}\n\nGenerated from template `{template}`.",
            "route": {
                "instanceId": route.selected_instance.instance_id,
                "serviceName": route.selected_instance.service_name,
                "reason": route.route_reason,
            },
        }
