from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from mcp_gateway.api.admin import create_admin_router
from mcp_gateway.api.response_envelope import failure
from mcp_gateway.api.tools import create_tools_router
from mcp_gateway.catalog.tool_catalog import ToolCatalog
from mcp_gateway.client.factory import create_mcp_client
from mcp_gateway.config.gateway_config import load_gateway_config
from mcp_gateway.discovery.factory import create_discovery_client
from mcp_gateway.domain.errors import GatewayError
from mcp_gateway.health.factory import create_health_checker
from mcp_gateway.observability.audit import create_audit_logger
from mcp_gateway.observability.metrics import MetricsRegistry
from mcp_gateway.observability.trace import ensure_request_id, ensure_trace_id
from mcp_gateway.policy.admin_authorizer import AdminAuthorizer
from mcp_gateway.policy.policy_checker import PolicyChecker
from mcp_gateway.policy.rate_limiter import RateLimiter
from mcp_gateway.routing.circuit_breaker import CircuitBreaker, create_circuit_breaker_store
from mcp_gateway.routing.router_scheduler import RouterScheduler
from mcp_gateway.runtime import GatewayRuntime
from mcp_gateway.schema.schema_registry import create_schema_registry


def create_app() -> FastAPI:
    config = load_gateway_config()
    discovery = create_discovery_client(config)
    health_checker = create_health_checker(config)
    catalog = ToolCatalog()
    metrics = MetricsRegistry()
    circuit_breaker = CircuitBreaker(
        enabled=config.circuit_breaker.enabled,
        failure_threshold=config.circuit_breaker.failure_threshold,
        recovery_seconds=config.circuit_breaker.recovery_seconds,
        store=create_circuit_breaker_store(
            config.state_backend.mode,
            config.state_backend.redis,
        ),
    )
    scheduler = RouterScheduler(catalog, circuit_breaker)
    runtime = GatewayRuntime(discovery, catalog, scheduler, health_checker, metrics)
    runtime.refresh_catalog()
    if config.catalog_refresh.enabled:
        runtime.start_auto_refresh(config.catalog_refresh.interval_seconds)
    mcp_client = create_mcp_client(config)
    policy_checker = PolicyChecker(config=config)
    rate_limiter = RateLimiter(config=config)
    admin_authorizer = AdminAuthorizer(config.admin)
    schema_registry = create_schema_registry(config)
    audit_logger = create_audit_logger(config)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            yield
        finally:
            runtime.stop_auto_refresh()

    app = FastAPI(title="MCP Gateway MVP", version="0.1.0", lifespan=lifespan)

    app.include_router(
        create_tools_router(
            catalog,
            scheduler,
            mcp_client,
            policy_checker,
            schema_registry,
            audit_logger,
            circuit_breaker,
            rate_limiter,
            metrics,
        )
    )
    app.include_router(create_admin_router(runtime, admin_authorizer))

    @app.get("/health")
    def health():
        last_refresh = runtime.last_refresh.__dict__ if runtime.last_refresh else None
        return {"status": "ok", "tools": len(catalog.list_tools()), "lastRefresh": last_refresh}

    @app.get("/metrics", response_class=PlainTextResponse)
    def metrics_endpoint():
        return PlainTextResponse(
            metrics.render_prometheus(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    @app.exception_handler(GatewayError)
    def handle_gateway_error(request: Request, exc: GatewayError):
        trace_id = ensure_trace_id(request.headers.get("x-trace-id"))
        request_id = ensure_request_id(request.headers.get("x-request-id"))
        return JSONResponse(
            status_code=exc.status_code,
            content=failure(exc.code.value, exc.message, trace_id, request_id).model_dump(),
        )

    return app


app = create_app()
