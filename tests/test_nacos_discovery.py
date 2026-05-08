import json

from mcp_gateway.config.gateway_config import NacosConfig
from mcp_gateway.discovery.nacos_discovery import NacosDiscoveryClient


def test_nacos_host_maps_to_internal_instance():
    host = {
        "instanceId": "knowledge-1",
        "ip": "10.0.0.12",
        "port": 18081,
        "weight": 100,
        "healthy": True,
        "metadata": {
            "metadataVersion": "1.0",
            "mcpProtocolVersion": "2025-03-26",
            "transport": "streamable-http",
            "endpoint": "/mcp",
            "healthPath": "/health",
            "domain": "knowledge",
            "serverVersion": "1.0.0",
            "toolSetVersion": "1.0.0",
            "tenantMode": "shared",
            "authType": "gateway-token",
            "enabled": True,
            "labels": ["test"],
            "tools": [
                {
                    "name": "knowledge.search",
                    "version": "1.0.0",
                    "description": "Search",
                    "inputSchemaRef": "nacos://in",
                    "outputSchemaRef": "nacos://out",
                    "readOnly": True,
                    "destructive": False,
                    "idempotent": True,
                    "enabled": True,
                }
            ],
        },
    }

    raw = NacosDiscoveryClient._to_raw_instance("mcp-server-knowledge", host)

    assert raw["service_name"] == "mcp-server-knowledge"
    assert raw["instance_id"] == "knowledge-1"
    assert raw["metadata"]["tools"][0]["name"] == "knowledge.search"


def test_nacos_host_supports_mcp_metadata_json_string():
    metadata = {
        "metadataVersion": "1.0",
        "mcpProtocolVersion": "2025-03-26",
        "transport": "streamable-http",
        "endpoint": "/mcp",
        "domain": "knowledge",
        "serverVersion": "1.0.0",
        "toolSetVersion": "1.0.0",
        "tools": [],
    }
    host = {
        "ip": "10.0.0.12",
        "port": 18081,
        "metadata": {"mcp": json.dumps(metadata)},
    }

    raw = NacosDiscoveryClient._to_raw_instance("mcp-server-knowledge", host)

    assert raw["metadata"]["metadataVersion"] == "1.0"


def test_nacos_host_supports_full_metadata_json_string():
    metadata = {
        "metadataVersion": "1.0",
        "mcpProtocolVersion": "2025-03-26",
        "transport": "streamable-http",
        "endpoint": "/mcp",
        "domain": "knowledge",
        "serverVersion": "1.0.0",
        "toolSetVersion": "1.0.0",
        "tools": [],
    }
    host = {
        "ip": "10.0.0.12",
        "port": 18081,
        "metadata": json.dumps(metadata),
    }

    raw = NacosDiscoveryClient._to_raw_instance("mcp-server-knowledge", host)

    assert raw["metadata"]["metadataVersion"] == "1.0"
