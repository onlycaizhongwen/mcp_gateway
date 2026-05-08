import pytest

from mcp_gateway.config.gateway_config import AdminConfig
from mcp_gateway.domain.errors import GatewayError
from mcp_gateway.policy.admin_authorizer import AdminAuthorizer


def test_admin_authorizer_allows_configured_app():
    authorizer = AdminAuthorizer(AdminConfig(allowed_app_ids=["admin-app"]))

    authorizer.ensure_allowed("admin-app")


def test_admin_authorizer_rejects_unconfigured_app():
    authorizer = AdminAuthorizer(AdminConfig(allowed_app_ids=["admin-app"]))

    with pytest.raises(GatewayError):
        authorizer.ensure_allowed("other-app")
