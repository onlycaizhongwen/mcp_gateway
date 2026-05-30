from __future__ import annotations

from time import perf_counter

from fastapi import APIRouter, Request

from mcp_gateway.api.response_envelope import success
from mcp_gateway.client.base import McpClient
from mcp_gateway.domain.errors import ErrorCode, GatewayError
from mcp_gateway.domain.models import ToolCallRequest
from mcp_gateway.observability.audit import AuditLogger, ToolCallAuditEvent
from mcp_gateway.observability.metrics import MetricsRegistry
from mcp_gateway.observability.trace import ensure_request_id, ensure_trace_id
from mcp_gateway.policy.auth_context import AuthContext
from mcp_gateway.policy.policy_checker import PolicyChecker
from mcp_gateway.policy.rate_limiter import RateLimiter
from mcp_gateway.routing.circuit_breaker import CircuitBreaker
from mcp_gateway.routing.router_scheduler import RouterScheduler
from mcp_gateway.catalog.tool_catalog import ToolCatalog
from mcp_gateway.schema.schema_registry import SchemaRegistry


def create_tools_router(
    catalog: ToolCatalog,
    scheduler: RouterScheduler,
    mcp_client: McpClient,
    policy_checker: PolicyChecker,
    schema_registry: SchemaRegistry,
    audit_logger: AuditLogger,
    circuit_breaker: CircuitBreaker | None = None,
    rate_limiter: RateLimiter | None = None,
    metrics: MetricsRegistry | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["tools"])

    @router.get("/tools")
    def list_tools(request: Request):
        trace_id = ensure_trace_id(request.headers.get("x-trace-id"))
        request_id = ensure_request_id(request.headers.get("x-request-id"))
        data = [
            {
                "name": tool.name,
                "version": tool.version,
                "domain": tool.domain,
                "description": tool.description,
                "inputSchemaRef": tool.input_schema_ref,
                "outputSchemaRef": tool.output_schema_ref,
                "readOnly": tool.read_only,
                "destructive": tool.destructive,
                "idempotent": tool.idempotent,
                "providers": len(tool.provider_instances),
            }
            for tool in catalog.list_tools()
        ]
        return success(data, trace_id, request_id)

    @router.get("/tools/{tool_name:path}/schema")
    def get_tool_schema(tool_name: str, request: Request):
        trace_id = ensure_trace_id(request.headers.get("x-trace-id"))
        request_id = ensure_request_id(request.headers.get("x-request-id"))
        tool = catalog.get_tool(tool_name)
        if tool is None:
            from mcp_gateway.domain.errors import ErrorCode, GatewayError

            raise GatewayError(ErrorCode.TOOL_NOT_FOUND, f"Tool not found: {tool_name}", 404)
        data = {
            "name": tool.name,
            "version": tool.version,
            "inputSchemaRef": tool.input_schema_ref,
            "outputSchemaRef": tool.output_schema_ref,
            "inputSchema": schema_registry.get_schema(tool.input_schema_ref),
            "outputSchema": schema_registry.get_schema(tool.output_schema_ref),
        }
        return success(data, trace_id, request_id)

    @router.post("/tools/{tool_name:path}/execute")
    def execute_tool(tool_name: str, body: ToolCallRequest, request: Request):
        started_at = perf_counter()
        trace_id = ensure_trace_id(body.trace_id or request.headers.get("x-trace-id"))
        request_id = ensure_request_id(body.request_id or request.headers.get("x-request-id"))
        context = AuthContext(tenant_id=body.tenant_id, app_id=body.app_id, user=body.user)
        route = None
        result_code = "0"
        try:
            policy_checker.ensure_allowed(context, tool_name)
            if rate_limiter is not None:
                rate_limiter.ensure_allowed(context, tool_name)
            route = scheduler.select_route(tool_name, tenant_id=body.tenant_id)
            tool = catalog.get_tool(tool_name, route.version)
            if tool is not None:
                schema_registry.validate_required(tool.input_schema_ref, body.arguments)
            result = mcp_client.call_tool(route, body.arguments)
            if circuit_breaker is not None:
                circuit_breaker.record_success(route.selected_instance.instance_id)
            return success(result, trace_id, request_id)
        except GatewayError as exc:
            result_code = exc.code.value
            if route is not None and exc.code in {
                ErrorCode.TOOL_DOWNSTREAM_TIMEOUT,
                ErrorCode.TOOL_EXECUTION_FAILED,
            }:
                if circuit_breaker is not None:
                    circuit_breaker.record_failure(route.selected_instance.instance_id)
            raise
        finally:
            duration_ms = (perf_counter() - started_at) * 1000
            audit_logger.record_tool_call(
                ToolCallAuditEvent(
                    trace_id=trace_id,
                    request_id=request_id,
                    app_id=body.app_id,
                    tenant_id=body.tenant_id,
                    tool_name=tool_name,
                    result_code=result_code,
                    duration_ms=duration_ms,
                    route_instance_id=route.selected_instance.instance_id if route else None,
                    route_service_name=route.selected_instance.service_name if route else None,
                    argument_keys=sorted(body.arguments.keys()),
                )
            )
            if metrics is not None:
                metrics.record_tool_call(tool_name, result_code, duration_ms)

    return router
