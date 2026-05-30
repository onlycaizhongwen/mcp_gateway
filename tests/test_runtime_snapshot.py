import pytest
import time

from mcp_gateway.catalog.tool_catalog import ToolCatalog
from mcp_gateway.discovery.mock_discovery import MockDiscoveryClient
from mcp_gateway.domain.models import McpServerInstance
from mcp_gateway.observability.metrics import MetricsRegistry
from mcp_gateway.routing.router_scheduler import RouterScheduler
from mcp_gateway.runtime import GatewayRuntime


class FailingDiscovery:
    def list_instances(self) -> list[McpServerInstance]:
        raise RuntimeError("nacos unavailable")


class FlakyDiscovery:
    def __init__(self) -> None:
        self._mock = MockDiscoveryClient()
        self.failed = False

    def list_instances(self) -> list[McpServerInstance]:
        if self.failed:
            raise RuntimeError("nacos unavailable")
        return self._mock.list_instances()


class CountingDiscovery:
    def __init__(self) -> None:
        self._mock = MockDiscoveryClient()
        self.calls = 0

    def list_instances(self) -> list[McpServerInstance]:
        self.calls += 1
        return self._mock.list_instances()


def test_runtime_keeps_last_catalog_snapshot_when_discovery_fails_after_success():
    catalog = ToolCatalog()
    discovery = FlakyDiscovery()
    runtime = GatewayRuntime(discovery, catalog, RouterScheduler(catalog))

    first = runtime.refresh_catalog()
    discovery.failed = True
    second = runtime.refresh_catalog()

    assert first.success is True
    assert second.success is False
    assert second.used_snapshot is True
    assert second.error_message == "nacos unavailable"
    assert second.tool_count == 3
    assert catalog.get_tool("knowledge.search") is not None
    assert catalog.get_tool("approval.create_task") is not None
    assert catalog.get_tool("document.generate") is not None


def test_runtime_raises_when_first_discovery_refresh_fails():
    catalog = ToolCatalog()
    runtime = GatewayRuntime(FailingDiscovery(), catalog, RouterScheduler(catalog))

    with pytest.raises(RuntimeError, match="nacos unavailable"):
        runtime.refresh_catalog()


def test_runtime_auto_refresh_runs_until_stopped():
    catalog = ToolCatalog()
    discovery = CountingDiscovery()
    runtime = GatewayRuntime(discovery, catalog, RouterScheduler(catalog))

    runtime.refresh_catalog()
    runtime.start_auto_refresh(0.1)
    time.sleep(0.25)
    runtime.stop_auto_refresh()
    calls_after_stop = discovery.calls
    time.sleep(0.15)

    assert calls_after_stop >= 2
    assert discovery.calls == calls_after_stop


def test_runtime_records_catalog_metrics_for_success_and_snapshot_failure():
    catalog = ToolCatalog()
    discovery = FlakyDiscovery()
    metrics = MetricsRegistry()
    runtime = GatewayRuntime(discovery, catalog, RouterScheduler(catalog), metrics=metrics)

    runtime.refresh_catalog()
    discovery.failed = True
    runtime.refresh_catalog()

    text = metrics.render_prometheus()
    assert 'mcp_gateway_catalog_refresh_total{result="success"} 1' in text
    assert 'mcp_gateway_catalog_refresh_total{result="snapshot"} 1' in text
    assert "mcp_gateway_catalog_tools 3" in text
