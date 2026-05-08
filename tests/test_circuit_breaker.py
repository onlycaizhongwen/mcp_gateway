from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from mcp_gateway.api.tools import create_tools_router
from mcp_gateway.catalog.tool_catalog import ToolCatalog
from mcp_gateway.discovery.mock_discovery import MockDiscoveryClient
from mcp_gateway.domain.errors import ErrorCode, GatewayError
from mcp_gateway.domain.models import ToolRoute
from mcp_gateway.observability.audit import InMemoryAuditLogger
from mcp_gateway.policy.policy_checker import PolicyChecker
from mcp_gateway.routing.circuit_breaker import CircuitBreaker
from mcp_gateway.routing.router_scheduler import RouterScheduler
from mcp_gateway.schema.schema_registry import SchemaRegistry


class ManualClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class FailingMcpClient:
    def call_tool(self, route: ToolRoute, arguments: dict[str, Any]) -> dict[str, Any]:
        raise GatewayError(ErrorCode.TOOL_EXECUTION_FAILED, "downstream failed", 502)


def build_catalog() -> ToolCatalog:
    catalog = ToolCatalog()
    catalog.refresh(MockDiscoveryClient().list_instances())
    return catalog


def test_circuit_breaker_opens_and_half_opens_after_recovery_window():
    clock = ManualClock()
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=10, now=clock)

    assert breaker.can_call("knowledge-1")
    breaker.record_failure("knowledge-1")
    assert breaker.can_call("knowledge-1")

    breaker.record_failure("knowledge-1")
    assert not breaker.can_call("knowledge-1")

    clock.advance(10)
    assert breaker.can_call("knowledge-1")

    breaker.record_success("knowledge-1")
    assert breaker.snapshot() == {}


def test_router_skips_open_instance():
    catalog = build_catalog()
    tool = catalog.get_tool("knowledge.search")
    assert tool is not None
    first_instance = tool.provider_instances[0]
    second_instance = first_instance.model_copy(update={"instance_id": "knowledge-2", "port": 18082})
    tool.provider_instances.append(second_instance)
    breaker = CircuitBreaker(failure_threshold=1, recovery_seconds=30)
    breaker.record_failure("knowledge-1")
    scheduler = RouterScheduler(catalog, breaker)

    route = scheduler.select_route("knowledge.search")

    assert route.selected_instance.instance_id == "knowledge-2"


def test_api_downstream_failure_records_circuit_breaker_failure():
    catalog = build_catalog()
    breaker = CircuitBreaker(failure_threshold=1, recovery_seconds=30)
    fastapi_app = FastAPI()
    fastapi_app.include_router(
        create_tools_router(
            catalog,
            RouterScheduler(catalog, breaker),
            FailingMcpClient(),
            PolicyChecker(allowed_tools={"internal-ai-agent": {"knowledge.search"}}),
            SchemaRegistry(),
            InMemoryAuditLogger(),
            breaker,
        )
    )

    @fastapi_app.exception_handler(GatewayError)
    def handle_gateway_error(_request, exc: GatewayError):
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=exc.status_code, content={"code": exc.code.value})

    client = TestClient(fastapi_app)

    response = client.post(
        "/api/v1/tools/knowledge.search/execute",
        json={
            "tenant_id": "tenant-a",
            "app_id": "internal-ai-agent",
            "arguments": {"query": "policy"},
        },
    )

    assert response.status_code == 502
    assert not breaker.can_call("knowledge-1")
