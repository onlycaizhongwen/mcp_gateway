from __future__ import annotations

from mcp_gateway.config.gateway_config import GatewayConfig
from mcp_gateway.health.health_checker import HealthChecker, HttpHealthChecker, NoopHealthChecker


def create_health_checker(config: GatewayConfig) -> HealthChecker:
    if config.health_check.enabled:
        return HttpHealthChecker(config.health_check)
    return NoopHealthChecker()
