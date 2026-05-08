from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class RateLimitConfig(BaseModel):
    qps: int | None = None
    burst: int | None = None


class AppPermissionConfig(BaseModel):
    app_id: str
    credential_ref: str | None = None
    tenants: list[str] = Field(default_factory=list)
    allowed_tools: list[str] = Field(default_factory=list)
    rate_limit: RateLimitConfig | None = None


class PermissionsConfig(BaseModel):
    apps: list[AppPermissionConfig] = Field(default_factory=list)


class DiscoveryConfig(BaseModel):
    mode: str = "mock"


class NacosConfig(BaseModel):
    enabled: bool = False
    endpoint: str = "http://127.0.0.1:8848"
    namespace: str | None = None
    group: str = "MCP_SERVER_GROUP"
    service_names: list[str] = Field(default_factory=list)
    username: str | None = None
    password: str | None = None
    timeout_seconds: float = 3


class McpClientConfig(BaseModel):
    mode: str = "mock"
    timeout_seconds: float = 10


class AdminConfig(BaseModel):
    allowed_app_ids: list[str] = Field(default_factory=list)


class CircuitBreakerConfig(BaseModel):
    enabled: bool = True
    failure_threshold: int = 3
    recovery_seconds: float = 30


class HealthCheckConfig(BaseModel):
    enabled: bool = False
    timeout_seconds: float = 1


class CatalogRefreshConfig(BaseModel):
    enabled: bool = False
    interval_seconds: float = 30


class GatewayConfig(BaseModel):
    discovery: DiscoveryConfig = Field(default_factory=DiscoveryConfig)
    mcp_client: McpClientConfig = Field(default_factory=McpClientConfig)
    admin: AdminConfig = Field(default_factory=AdminConfig)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)
    catalog_refresh: CatalogRefreshConfig = Field(default_factory=CatalogRefreshConfig)
    nacos: NacosConfig = Field(default_factory=NacosConfig)
    permissions: PermissionsConfig = Field(default_factory=PermissionsConfig)


def default_config_path() -> Path:
    return Path(__file__).resolve().parents[3] / "config" / "mcp-gateway.yaml"


def load_gateway_config(path: str | Path | None = None) -> GatewayConfig:
    config_path = Path(path or os.getenv("MCP_GATEWAY_CONFIG", default_config_path()))
    if not config_path.exists():
        return GatewayConfig()

    with config_path.open("r", encoding="utf-8") as file:
        raw = yaml.safe_load(file) or {}
    return GatewayConfig.model_validate(raw)
