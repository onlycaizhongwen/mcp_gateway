from __future__ import annotations

from fastapi import APIRouter, Request

from mcp_gateway.api.response_envelope import success
from mcp_gateway.observability.trace import ensure_request_id, ensure_trace_id
from mcp_gateway.policy.admin_authorizer import AdminAuthorizer
from mcp_gateway.runtime import GatewayRuntime


def create_admin_router(runtime: GatewayRuntime, authorizer: AdminAuthorizer) -> APIRouter:
    router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

    @router.get("/catalog/status")
    def catalog_status(request: Request):
        authorizer.ensure_allowed(request.headers.get("x-app-id"))
        trace_id = ensure_trace_id(request.headers.get("x-trace-id"))
        request_id = ensure_request_id(request.headers.get("x-request-id"))
        last_refresh = runtime.last_refresh
        data = {
            "tools": len(runtime.catalog.list_tools()),
            "instances": last_refresh.instance_count if last_refresh else 0,
            "healthyInstances": last_refresh.healthy_instance_count if last_refresh else 0,
            "unavailableInstances": last_refresh.unavailable_instance_count if last_refresh else 0,
            "lastRefresh": last_refresh.__dict__ if last_refresh else None,
        }
        return success(data, trace_id, request_id)

    @router.post("/catalog/refresh")
    def refresh_catalog(request: Request):
        authorizer.ensure_allowed(request.headers.get("x-app-id"))
        trace_id = ensure_trace_id(request.headers.get("x-trace-id"))
        request_id = ensure_request_id(request.headers.get("x-request-id"))
        result = runtime.refresh_catalog()
        return success(result.__dict__, trace_id, request_id)

    return router
