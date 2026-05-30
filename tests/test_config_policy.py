from pathlib import Path

import pytest

from mcp_gateway.config.gateway_config import load_gateway_config
from mcp_gateway.domain.errors import GatewayError
from mcp_gateway.policy.auth_context import AuthContext
from mcp_gateway.policy.policy_checker import PolicyChecker


def test_load_gateway_config_from_yaml(tmp_path: Path):
    config_file = tmp_path / "gateway.yaml"
    config_file.write_text(
        """
permissions:
  apps:
    - app_id: app-a
      credential_ref: kms://app-a
      tenants: [tenant-a]
      allowed_tools: [knowledge.search]
""",
        encoding="utf-8",
    )

    config = load_gateway_config(config_file)

    assert config.permissions.apps[0].app_id == "app-a"
    assert config.permissions.apps[0].allowed_tools == ["knowledge.search"]


def test_load_circuit_breaker_config_from_yaml(tmp_path: Path):
    config_file = tmp_path / "gateway.yaml"
    config_file.write_text(
        """
circuit_breaker:
  enabled: true
  failure_threshold: 5
  recovery_seconds: 60
""",
        encoding="utf-8",
    )

    config = load_gateway_config(config_file)

    assert config.circuit_breaker.enabled is True
    assert config.circuit_breaker.failure_threshold == 5
    assert config.circuit_breaker.recovery_seconds == 60


def test_load_rate_limit_config_from_yaml(tmp_path: Path):
    config_file = tmp_path / "gateway.yaml"
    config_file.write_text(
        """
permissions:
  apps:
    - app_id: app-a
      allowed_tools: [knowledge.search]
      rate_limit:
        qps: 3
        burst: 7
""",
        encoding="utf-8",
    )

    config = load_gateway_config(config_file)

    assert config.permissions.apps[0].rate_limit is not None
    assert config.permissions.apps[0].rate_limit.qps == 3
    assert config.permissions.apps[0].rate_limit.burst == 7


def test_load_health_check_config_from_yaml(tmp_path: Path):
    config_file = tmp_path / "gateway.yaml"
    config_file.write_text(
        """
health_check:
  enabled: true
  timeout_seconds: 2
""",
        encoding="utf-8",
    )

    config = load_gateway_config(config_file)

    assert config.health_check.enabled is True
    assert config.health_check.timeout_seconds == 2


def test_load_catalog_refresh_config_from_yaml(tmp_path: Path):
    config_file = tmp_path / "gateway.yaml"
    config_file.write_text(
        """
catalog_refresh:
  enabled: true
  interval_seconds: 15
""",
        encoding="utf-8",
    )

    config = load_gateway_config(config_file)

    assert config.catalog_refresh.enabled is True
    assert config.catalog_refresh.interval_seconds == 15


def test_load_schema_registry_config_from_yaml(tmp_path: Path):
    config_file = tmp_path / "gateway.yaml"
    config_file.write_text(
        """
schema_registry:
  mode: nacos_config
  nacos_config:
    endpoint: http://nacos.example.com:8848
    namespace: dev
    group: MCP_SCHEMA_GROUP
    timeout_seconds: 4
""",
        encoding="utf-8",
    )

    config = load_gateway_config(config_file)

    assert config.schema_registry.mode == "nacos_config"
    assert config.schema_registry.nacos_config.endpoint == "http://nacos.example.com:8848"
    assert config.schema_registry.nacos_config.namespace == "dev"
    assert config.schema_registry.nacos_config.group == "MCP_SCHEMA_GROUP"
    assert config.schema_registry.nacos_config.timeout_seconds == 4


def test_load_audit_config_from_yaml(tmp_path: Path):
    config_file = tmp_path / "gateway.yaml"
    config_file.write_text(
        """
audit:
  mode: file
  file:
    path: logs/custom-audit.jsonl
""",
        encoding="utf-8",
    )

    config = load_gateway_config(config_file)

    assert config.audit.mode == "file"
    assert config.audit.file.path == "logs/custom-audit.jsonl"


def test_policy_checker_uses_config():
    config = load_gateway_config("config/mcp-gateway.yaml")
    checker = PolicyChecker(config=config)

    checker.ensure_allowed(
        AuthContext(app_id="internal-ai-agent", tenant_id="tenant-a"),
        "knowledge.search",
    )


def test_policy_checker_rejects_wrong_tenant():
    config = load_gateway_config("config/mcp-gateway.yaml")
    checker = PolicyChecker(config=config)

    with pytest.raises(GatewayError):
        checker.ensure_allowed(
            AuthContext(app_id="demo-app", tenant_id="tenant-x"),
            "knowledge.search",
        )
