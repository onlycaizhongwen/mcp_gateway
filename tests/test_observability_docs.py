from pathlib import Path

import yaml


def test_prometheus_alert_rules_cover_core_gateway_signals():
    rules_file = Path("deploy/prometheus/mcp-gateway-alerts.yml")

    data = yaml.safe_load(rules_file.read_text(encoding="utf-8"))

    rules = data["groups"][0]["rules"]
    alert_names = {rule["alert"] for rule in rules}
    assert {
        "McpGatewayToolErrorRateHigh",
        "McpGatewayToolRateLimitedHigh",
        "McpGatewayServerUnavailable",
        "McpGatewayCatalogRefreshFailed",
        "McpGatewayNoHealthyInstances",
        "McpGatewayAverageLatencyHigh",
    }.issubset(alert_names)

    expressions = "\n".join(rule["expr"] for rule in rules)
    assert "mcp_gateway_tool_calls_total" in expressions
    assert "MCP_RATE_LIMITED" in expressions
    assert "MCP_SERVER_UNAVAILABLE" in expressions
    assert "mcp_gateway_catalog_refresh_total" in expressions
    assert "mcp_gateway_catalog_healthy_instances" in expressions
