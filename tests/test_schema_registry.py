import json
from urllib.parse import parse_qs, urlparse

import pytest

from mcp_gateway.config.gateway_config import (
    GatewayConfig,
    NacosConfig,
    NacosConfigStoreConfig,
    SchemaRegistryConfig,
)
from mcp_gateway.domain.errors import GatewayError
from mcp_gateway.schema.schema_registry import (
    NacosConfigSchemaRegistry,
    SchemaRegistry,
    create_schema_registry,
)


def test_schema_registry_returns_schema_by_ref():
    registry = SchemaRegistry()

    schema = registry.get_schema("nacos://mcp-schemas/knowledge.search/1.0.0/input")

    assert schema["required"] == ["query"]


def test_schema_registry_returns_document_schema_by_ref():
    registry = SchemaRegistry()

    schema = registry.get_schema("nacos://mcp-schemas/document.generate/1.0.0/input")

    assert schema["required"] == ["template", "title"]


def test_schema_registry_validates_required_arguments():
    registry = SchemaRegistry()

    registry.validate_required(
        "nacos://mcp-schemas/knowledge.search/1.0.0/input",
        {"query": "年假政策"},
    )


def test_schema_registry_rejects_missing_required_arguments():
    registry = SchemaRegistry()

    with pytest.raises(GatewayError):
        registry.validate_required(
            "nacos://mcp-schemas/knowledge.search/1.0.0/input",
            {},
        )


def test_nacos_config_schema_registry_loads_schema(monkeypatch):
    requests = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return json.dumps({"type": "object", "required": ["query"]}).encode("utf-8")

    def fake_urlopen(request, timeout):
        requests.append((request.full_url, timeout))
        return FakeResponse()

    monkeypatch.setattr("mcp_gateway.schema.schema_registry.urlopen", fake_urlopen)
    registry = NacosConfigSchemaRegistry(
        NacosConfigStoreConfig(
            endpoint="http://127.0.0.1:8848",
            namespace="dev",
            group="MCP_SCHEMA_GROUP",
            timeout_seconds=2,
        )
    )

    schema = registry.get_schema("nacos://mcp-schemas/knowledge.search/1.0.0/input")
    cached_schema = registry.get_schema("nacos://mcp-schemas/knowledge.search/1.0.0/input")

    assert schema["required"] == ["query"]
    assert cached_schema == schema
    assert len(requests) == 1
    url, timeout = requests[0]
    params = parse_qs(urlparse(url).query)
    assert timeout == 2
    assert params["dataId"] == ["mcp-schemas__knowledge.search__1.0.0__input.json"]
    assert params["group"] == ["MCP_SCHEMA_GROUP"]
    assert params["tenant"] == ["dev"]


def test_nacos_config_schema_registry_uses_access_token(monkeypatch):
    requests = []

    class FakeResponse:
        def __init__(self, payload: bytes):
            self._payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return self._payload

    def fake_urlopen(request, timeout):
        requests.append(request)
        if request.full_url.endswith("/nacos/v1/auth/login"):
            return FakeResponse(json.dumps({"accessToken": "token-a"}).encode("utf-8"))
        return FakeResponse(json.dumps({"type": "object"}).encode("utf-8"))

    monkeypatch.setattr("mcp_gateway.schema.schema_registry.urlopen", fake_urlopen)
    registry = NacosConfigSchemaRegistry(
        NacosConfigStoreConfig(
            endpoint="http://127.0.0.1:8848",
            username="nacos",
            password="nacos",
        )
    )

    registry.get_schema("nacos://mcp-schemas/knowledge.search/1.0.0/input")

    assert len(requests) == 2
    params = parse_qs(urlparse(requests[1].full_url).query)
    assert params["accessToken"] == ["token-a"]


def test_nacos_config_schema_registry_rejects_invalid_schema_ref():
    registry = NacosConfigSchemaRegistry(NacosConfigStoreConfig(endpoint="http://127.0.0.1:8848"))

    with pytest.raises(GatewayError):
        registry.get_schema("file://schema.json")


def test_create_schema_registry_inherits_nacos_defaults():
    config = GatewayConfig(
        nacos=NacosConfig(
            endpoint="http://nacos.example.com:8848",
            namespace="dev",
            username="nacos",
            password="secret",
            timeout_seconds=4,
        ),
        schema_registry=SchemaRegistryConfig(mode="nacos_config"),
    )

    registry = create_schema_registry(config)

    assert isinstance(registry, NacosConfigSchemaRegistry)
    assert registry._config.endpoint == "http://nacos.example.com:8848"
    assert registry._config.namespace == "dev"
    assert registry._config.username == "nacos"
    assert registry._config.password == "secret"
    assert registry._config.timeout_seconds == 4
