from fastapi.testclient import TestClient

from mcp_gateway.main import create_app


def test_catalog_status_api():
    client = TestClient(create_app())

    response = client.get(
        "/api/v1/admin/catalog/status",
        headers={"x-app-id": "internal-ai-agent"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "0"
    assert body["data"]["tools"] == 3
    assert body["data"]["instances"] == 3
    assert body["data"]["healthyInstances"] == 3
    assert body["data"]["unavailableInstances"] == 0
    assert body["data"]["lastRefresh"]["tool_count"] == 3
    assert body["data"]["lastRefresh"]["healthy_instance_count"] == 3
    assert body["data"]["lastRefresh"]["success"] is True
    assert body["data"]["lastRefresh"]["used_snapshot"] is False


def test_catalog_refresh_api():
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/admin/catalog/refresh",
        headers={"x-app-id": "internal-ai-agent"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "0"
    assert body["data"]["instance_count"] == 3
    assert body["data"]["healthy_instance_count"] == 3
    assert body["data"]["unavailable_instance_count"] == 0
    assert body["data"]["tool_count"] == 3
    assert body["data"]["success"] is True


def test_catalog_admin_api_rejects_missing_app_id():
    client = TestClient(create_app())

    response = client.get("/api/v1/admin/catalog/status")

    assert response.status_code == 403
    assert response.json()["code"] == "MCP_TOOL_PERMISSION_DENIED"
