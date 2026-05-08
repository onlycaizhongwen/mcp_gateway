from fastapi.testclient import TestClient

from mcp_gateway.api.tools import create_tools_router
from mcp_gateway.catalog.tool_catalog import ToolCatalog
from mcp_gateway.client.mock_mcp_client import MockMcpClient
from mcp_gateway.discovery.mock_discovery import MockDiscoveryClient
from mcp_gateway.main import create_app
from mcp_gateway.observability.audit import InMemoryAuditLogger
from mcp_gateway.policy.policy_checker import PolicyChecker
from mcp_gateway.routing.router_scheduler import RouterScheduler
from mcp_gateway.schema.schema_registry import SchemaRegistry


def test_list_tools_api():
    client = TestClient(create_app())

    response = client.get("/api/v1/tools")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "0"
    assert {tool["name"] for tool in body["data"]} == {
        "knowledge.search",
        "approval.create_task",
        "document.generate",
    }


def test_execute_knowledge_search_api():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/tools/knowledge.search/execute",
        json={
            "tenant_id": "tenant-a",
            "app_id": "internal-ai-agent",
            "arguments": {"query": "年假政策", "top_k": 1},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "0"
    assert body["data"]["answer"] == "Mock answer for: 年假政策"
    assert body["data"]["route"]["instanceId"] == "knowledge-1"


def test_get_tool_schema_api():
    client = TestClient(create_app())

    response = client.get("/api/v1/tools/knowledge.search/schema")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "0"
    assert body["data"]["inputSchema"]["required"] == ["query"]
    assert body["data"]["outputSchema"]["required"] == ["answer"]


def test_get_approval_tool_schema_api():
    client = TestClient(create_app())

    response = client.get("/api/v1/tools/approval.create_task/schema")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "0"
    assert body["data"]["inputSchema"]["required"] == ["title", "applicant", "approver"]


def test_execute_knowledge_search_validates_required_schema():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/tools/knowledge.search/execute",
        json={
            "tenant_id": "tenant-a",
            "app_id": "internal-ai-agent",
            "arguments": {},
        },
    )

    assert response.status_code == 400
    assert response.json()["code"] == "MCP_TOOL_VALIDATION_FAILED"


def test_execute_unknown_tool_returns_404():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/tools/budget.forecast/execute",
        json={
            "tenant_id": "tenant-a",
            "app_id": "internal-ai-agent",
            "arguments": {},
        },
    )

    assert response.status_code == 403
    assert response.json()["code"] == "MCP_TOOL_PERMISSION_DENIED"


def test_execute_approval_create_task_api():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/tools/approval.create_task/execute",
        json={
            "tenant_id": "tenant-a",
            "app_id": "internal-ai-agent",
            "arguments": {
                "title": "合同审批",
                "applicant": "u001",
                "approver": "u002",
                "payload": {"amount": 1000},
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "0"
    assert body["data"]["taskId"] == "mock-approval-001"
    assert body["data"]["route"]["instanceId"] == "approval-1"


def test_execute_document_generate_api():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/tools/document.generate/execute",
        json={
            "tenant_id": "tenant-a",
            "app_id": "internal-ai-agent",
            "arguments": {
                "template": "contract.summary",
                "title": "合同摘要",
                "variables": {"customer": "示例客户"},
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "0"
    assert body["data"]["documentId"] == "mock-document-001"
    assert body["data"]["route"]["instanceId"] == "document-1"


def test_demo_app_cannot_call_approval_tool():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/tools/approval.create_task/execute",
        json={
            "tenant_id": "tenant-a",
            "app_id": "demo-app",
            "arguments": {
                "title": "合同审批",
                "applicant": "u001",
                "approver": "u002",
            },
        },
    )

    assert response.status_code == 403
    assert response.json()["code"] == "MCP_TOOL_PERMISSION_DENIED"


def test_execute_tool_writes_audit_event():
    catalog = ToolCatalog()
    catalog.refresh(MockDiscoveryClient().list_instances())
    audit_logger = InMemoryAuditLogger()
    app = create_app()
    app.router.routes.clear()
    app.include_router(
        create_tools_router(
            catalog,
            RouterScheduler(catalog),
            MockMcpClient(),
            PolicyChecker(allowed_tools={"internal-ai-agent": {"knowledge.search"}}),
            SchemaRegistry(),
            audit_logger,
        )
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/tools/knowledge.search/execute",
        json={
            "tenant_id": "tenant-a",
            "app_id": "internal-ai-agent",
            "arguments": {"query": "年假政策", "top_k": 1},
        },
    )

    assert response.status_code == 200
    assert audit_logger.events[0].tool_name == "knowledge.search"
    assert audit_logger.events[0].result_code == "0"
    assert audit_logger.events[0].argument_keys == ["query", "top_k"]
    assert audit_logger.events[0].route_instance_id == "knowledge-1"
