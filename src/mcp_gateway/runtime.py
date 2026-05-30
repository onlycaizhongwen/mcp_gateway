from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timezone

from mcp_gateway.catalog.tool_catalog import ToolCatalog
from mcp_gateway.discovery.base import DiscoveryClient
from mcp_gateway.health.health_checker import HealthChecker, NoopHealthChecker, apply_health_checks
from mcp_gateway.observability.metrics import MetricsRegistry
from mcp_gateway.routing.router_scheduler import RouterScheduler


logger = logging.getLogger(__name__)


@dataclass
class CatalogRefreshResult:
    refreshed_at: str
    instance_count: int
    healthy_instance_count: int
    unavailable_instance_count: int
    tool_count: int
    success: bool = True
    used_snapshot: bool = False
    error_message: str | None = None


class GatewayRuntime:
    def __init__(
        self,
        discovery: DiscoveryClient,
        catalog: ToolCatalog,
        scheduler: RouterScheduler,
        health_checker: HealthChecker | None = None,
        metrics: MetricsRegistry | None = None,
    ) -> None:
        self.discovery = discovery
        self.catalog = catalog
        self.scheduler = scheduler
        self.health_checker = health_checker or NoopHealthChecker()
        self.metrics = metrics
        self.last_refresh: CatalogRefreshResult | None = None
        self._refresh_thread: threading.Thread | None = None
        self._stop_refresh = threading.Event()

    def refresh_catalog(self) -> CatalogRefreshResult:
        try:
            instances = self.discovery.list_instances()
        except Exception as exc:
            if self.last_refresh is None:
                raise
            self.last_refresh = CatalogRefreshResult(
                refreshed_at=datetime.now(timezone.utc).isoformat(),
                instance_count=self.last_refresh.instance_count,
                healthy_instance_count=self.last_refresh.healthy_instance_count,
                unavailable_instance_count=self.last_refresh.unavailable_instance_count,
                tool_count=len(self.catalog.list_tools()),
                success=False,
                used_snapshot=True,
                error_message=str(exc),
            )
            if self.metrics is not None:
                self.metrics.record_catalog_refresh(self.last_refresh)
            return self.last_refresh

        checked_instances = apply_health_checks(instances, self.health_checker)
        healthy_instance_count = sum(1 for instance in checked_instances if instance.healthy)
        self.catalog.refresh(checked_instances)
        self.last_refresh = CatalogRefreshResult(
            refreshed_at=datetime.now(timezone.utc).isoformat(),
            instance_count=len(instances),
            healthy_instance_count=healthy_instance_count,
            unavailable_instance_count=len(checked_instances) - healthy_instance_count,
            tool_count=len(self.catalog.list_tools()),
        )
        if self.metrics is not None:
            self.metrics.record_catalog_refresh(self.last_refresh)
        return self.last_refresh

    def start_auto_refresh(self, interval_seconds: float) -> None:
        if self._refresh_thread is not None and self._refresh_thread.is_alive():
            return

        interval = max(0.1, interval_seconds)
        self._stop_refresh.clear()

        def refresh_loop() -> None:
            while not self._stop_refresh.wait(interval):
                try:
                    self.refresh_catalog()
                except Exception:
                    logger.exception("catalog auto refresh failed")

        self._refresh_thread = threading.Thread(
            target=refresh_loop,
            name="mcp-catalog-refresh",
            daemon=True,
        )
        self._refresh_thread.start()

    def stop_auto_refresh(self) -> None:
        self._stop_refresh.set()
        if self._refresh_thread is not None:
            self._refresh_thread.join(timeout=5)
            self._refresh_thread = None
