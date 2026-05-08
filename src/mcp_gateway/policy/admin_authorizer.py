from __future__ import annotations

from mcp_gateway.config.gateway_config import AdminConfig
from mcp_gateway.domain.errors import ErrorCode, GatewayError


class AdminAuthorizer:
    def __init__(self, config: AdminConfig) -> None:
        self._allowed_app_ids = set(config.allowed_app_ids)

    def ensure_allowed(self, app_id: str | None) -> None:
        if not app_id:
            raise GatewayError(ErrorCode.TOOL_PERMISSION_DENIED, "Missing admin app id", 403)
        if app_id not in self._allowed_app_ids:
            raise GatewayError(
                ErrorCode.TOOL_PERMISSION_DENIED,
                f"App {app_id} is not allowed to access admin APIs",
                403,
            )
