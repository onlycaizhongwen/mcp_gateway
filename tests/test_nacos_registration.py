from __future__ import annotations

import json
from urllib.parse import parse_qs

from mcp_gateway.examples.nacos_registration import (
    McpServerRegistration,
    NacosMcpServerRegistrar,
    NacosRegistrationConfig,
    knowledge_search_metadata,
)


class FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self._body.encode("utf-8")


def test_register_instance_posts_nacos_form(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["timeout"] = timeout
        captured["body"] = request.data.decode("utf-8")
        return FakeResponse("ok")

    monkeypatch.setattr("mcp_gateway.examples.nacos_registration.urlopen", fake_urlopen)
    registrar = NacosMcpServerRegistrar(
        NacosRegistrationConfig(
            endpoint="http://nacos.local:8848",
            namespace="dev",
            group="MCP_SERVER_GROUP",
            timeout_seconds=5,
        )
    )

    result = registrar.register_instance(
        McpServerRegistration(
            service_name="mcp-server-knowledge",
            ip="10.0.0.12",
            port=18081,
            metadata=knowledge_search_metadata(),
        )
    )

    body = parse_qs(captured["body"])
    metadata = json.loads(body["metadata"][0])

    assert result == "ok"
    assert captured["url"] == "http://nacos.local:8848/nacos/v1/ns/instance"
    assert captured["method"] == "POST"
    assert captured["timeout"] == 5
    assert body["serviceName"] == ["mcp-server-knowledge"]
    assert body["groupName"] == ["MCP_SERVER_GROUP"]
    assert body["namespaceId"] == ["dev"]
    assert body["ip"] == ["10.0.0.12"]
    assert body["port"] == ["18081"]
    assert metadata["tools"][0]["name"] == "knowledge.search"


def test_register_instance_uses_access_token(monkeypatch):
    captured_bodies = []

    def fake_urlopen(request, timeout):
        captured_bodies.append(request.data.decode("utf-8"))
        if request.full_url.endswith("/nacos/v1/auth/login"):
            return FakeResponse('{"accessToken":"token-1"}')
        return FakeResponse("ok")

    monkeypatch.setattr("mcp_gateway.examples.nacos_registration.urlopen", fake_urlopen)
    registrar = NacosMcpServerRegistrar(
        NacosRegistrationConfig(username="nacos", password="secret")
    )

    registrar.register_instance(
        McpServerRegistration(
            service_name="mcp-server-knowledge",
            ip="10.0.0.12",
            port=18081,
            metadata=knowledge_search_metadata(),
        )
    )

    register_body = parse_qs(captured_bodies[-1])

    assert parse_qs(captured_bodies[0]) == {"username": ["nacos"], "password": ["secret"]}
    assert register_body["accessToken"] == ["token-1"]


def test_deregister_instance_posts_delete_form(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["method"] = request.get_method()
        captured["body"] = request.data.decode("utf-8")
        return FakeResponse("ok")

    monkeypatch.setattr("mcp_gateway.examples.nacos_registration.urlopen", fake_urlopen)
    registrar = NacosMcpServerRegistrar(NacosRegistrationConfig(namespace="dev"))

    result = registrar.deregister_instance("mcp-server-knowledge", "10.0.0.12", 18081)

    body = parse_qs(captured["body"])

    assert result == "ok"
    assert captured["method"] == "DELETE"
    assert body["serviceName"] == ["mcp-server-knowledge"]
    assert body["namespaceId"] == ["dev"]
