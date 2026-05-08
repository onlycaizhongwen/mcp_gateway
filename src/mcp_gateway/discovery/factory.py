from __future__ import annotations

from mcp_gateway.config.gateway_config import GatewayConfig
from mcp_gateway.discovery.base import DiscoveryClient
from mcp_gateway.discovery.mock_discovery import MockDiscoveryClient
from mcp_gateway.discovery.nacos_discovery import NacosDiscoveryClient


def create_discovery_client(config: GatewayConfig) -> DiscoveryClient:
    if config.nacos.enabled or config.discovery.mode == "nacos":
        return NacosDiscoveryClient(config.nacos)
    return MockDiscoveryClient()
