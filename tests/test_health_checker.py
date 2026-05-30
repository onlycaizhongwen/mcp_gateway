from mcp_gateway.catalog.tool_catalog import ToolCatalog
from mcp_gateway.discovery.mock_discovery import MockDiscoveryClient
from mcp_gateway.domain.models import McpServerInstance
from mcp_gateway.health.health_checker import apply_health_checks
from mcp_gateway.routing.router_scheduler import RouterScheduler
from mcp_gateway.runtime import GatewayRuntime


class FixedHealthChecker:
    def __init__(self, healthy: bool) -> None:
        self._healthy = healthy

    def is_healthy(self, instance: McpServerInstance) -> bool:
        return self._healthy


def test_apply_health_checks_marks_instance_unhealthy():
    instances = MockDiscoveryClient().list_instances()

    checked = apply_health_checks(instances, FixedHealthChecker(healthy=False))

    assert checked[0].healthy is False
    assert instances[0].healthy is True


def test_apply_health_checks_can_recover_discovery_unhealthy_instance():
    instances = [
        MockDiscoveryClient().list_instances()[0].model_copy(update={"healthy": False})
    ]

    checked = apply_health_checks(instances, FixedHealthChecker(healthy=True))

    assert checked[0].healthy is True
    assert instances[0].healthy is False


def test_runtime_excludes_failed_health_check_from_catalog():
    catalog = ToolCatalog()
    runtime = GatewayRuntime(
        MockDiscoveryClient(),
        catalog,
        RouterScheduler(catalog),
        FixedHealthChecker(healthy=False),
    )

    result = runtime.refresh_catalog()

    assert result.instance_count == 3
    assert result.healthy_instance_count == 0
    assert result.unavailable_instance_count == 3
    assert result.tool_count == 3
    assert catalog.get_tool("knowledge.search") is not None
    assert catalog.get_tool("knowledge.search").provider_instances == []
