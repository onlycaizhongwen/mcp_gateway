from mcp_gateway.observability.metrics import MetricsRegistry
from mcp_gateway.runtime import CatalogRefreshResult


def test_metrics_registry_renders_prometheus_text():
    metrics = MetricsRegistry()

    metrics.record_tool_call('knowledge.search"test', "0", 12.5)

    text = metrics.render_prometheus()

    assert "# TYPE mcp_gateway_tool_calls_total counter" in text
    assert (
        'mcp_gateway_tool_calls_total{result_code="0",tool_name="knowledge.search\\"test"} 1'
        in text
    )
    assert (
        'mcp_gateway_tool_call_duration_ms_sum{result_code="0",tool_name="knowledge.search\\"test"} 12.5'
        in text
    )


def test_metrics_registry_records_catalog_refresh_snapshot():
    metrics = MetricsRegistry()

    metrics.record_catalog_refresh(
        CatalogRefreshResult(
            refreshed_at="2026-05-29T00:00:00+00:00",
            instance_count=3,
            healthy_instance_count=2,
            unavailable_instance_count=1,
            tool_count=3,
            success=False,
            used_snapshot=True,
        )
    )

    text = metrics.render_prometheus()

    assert 'mcp_gateway_catalog_refresh_total{result="snapshot"} 1' in text
    assert "mcp_gateway_catalog_tools 3" in text
    assert "mcp_gateway_catalog_instances 3" in text
    assert "mcp_gateway_catalog_healthy_instances 2" in text
    assert "mcp_gateway_catalog_unavailable_instances 1" in text
