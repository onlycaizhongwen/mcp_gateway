from __future__ import annotations

from mcp_gateway.config.gateway_config import GatewayConfig
from mcp_gateway.domain.errors import ErrorCode, GatewayError
from mcp_gateway.policy.auth_context import AuthContext


class PolicyChecker:
    def __init__(
        self,
        allowed_tools: dict[str, set[str]] | None = None,
        config: GatewayConfig | None = None,
    ) -> None:
        if allowed_tools is not None:
            self._allowed_tools = allowed_tools
            self._allowed_tenants: dict[str, set[str]] = {}
            return

        self._allowed_tools = {}
        self._allowed_tenants = {}
        if config is not None:
            for app in config.permissions.apps:
                self._allowed_tools[app.app_id] = set(app.allowed_tools)
                self._allowed_tenants[app.app_id] = set(app.tenants)

    def ensure_allowed(self, context: AuthContext, tool_name: str) -> None:
        if not context.app_id:
            raise GatewayError(ErrorCode.TOOL_PERMISSION_DENIED, "Missing app_id", 403)

        allowed_tenants = self._allowed_tenants.get(context.app_id, set())
        if allowed_tenants and context.tenant_id not in allowed_tenants:
            raise GatewayError(
                ErrorCode.TOOL_PERMISSION_DENIED,
                f"App {context.app_id} is not allowed in tenant {context.tenant_id}",
                403,
            )

        allowed = self._allowed_tools.get(context.app_id, set())
        if tool_name not in allowed:
            raise GatewayError(
                ErrorCode.TOOL_PERMISSION_DENIED,
                f"App {context.app_id} is not allowed to call {tool_name}",
                403,
            )
