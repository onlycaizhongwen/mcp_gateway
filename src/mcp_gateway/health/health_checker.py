from __future__ import annotations

from typing import Protocol
from urllib.error import URLError
from urllib.request import Request, urlopen

from mcp_gateway.config.gateway_config import HealthCheckConfig
from mcp_gateway.domain.models import McpServerInstance


class HealthChecker(Protocol):
    def is_healthy(self, instance: McpServerInstance) -> bool:
        """Return whether the instance passes the gateway-side health check."""


class NoopHealthChecker:
    def is_healthy(self, instance: McpServerInstance) -> bool:
        return True


class HttpHealthChecker:
    def __init__(self, config: HealthCheckConfig) -> None:
        self._config = config

    def is_healthy(self, instance: McpServerInstance) -> bool:
        url = f"http://{instance.host}:{instance.port}{instance.metadata.health_path}"
        request = Request(url, method="GET")
        try:
            with urlopen(request, timeout=self._config.timeout_seconds) as response:
                return 200 <= response.status < 400
        except (TimeoutError, URLError, OSError):
            return False


def apply_health_checks(
    instances: list[McpServerInstance],
    checker: HealthChecker,
) -> list[McpServerInstance]:
    checked: list[McpServerInstance] = []
    for instance in instances:
        healthy = instance.healthy and checker.is_healthy(instance)
        checked.append(instance.model_copy(update={"healthy": healthy}))
    return checked
