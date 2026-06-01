from __future__ import annotations

import json
from urllib.parse import parse_qs

from mcp_gateway.examples.nacos_registration import (
    McpServerNacosLifecycle,
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
    mcp_metadata = json.loads(metadata["mcp"])
    assert mcp_metadata["tools"][0]["name"] == "knowledge.search"


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


def test_send_heartbeat_puts_nacos_beat_form(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["body"] = request.data.decode("utf-8")
        return FakeResponse("ok")

    monkeypatch.setattr("mcp_gateway.examples.nacos_registration.urlopen", fake_urlopen)
    registrar = NacosMcpServerRegistrar(NacosRegistrationConfig(namespace="dev"))

    result = registrar.send_heartbeat(
        McpServerRegistration(
            service_name="mcp-server-knowledge",
            ip="10.0.0.12",
            port=18081,
            metadata=knowledge_search_metadata(),
            ephemeral=True,
        )
    )

    body = parse_qs(captured["body"])
    beat = json.loads(body["beat"][0])

    assert result == "ok"
    assert captured["url"] == "http://127.0.0.1:8848/nacos/v1/ns/instance/beat"
    assert captured["method"] == "PUT"
    assert body["serviceName"] == ["mcp-server-knowledge"]
    assert body["namespaceId"] == ["dev"]
    assert body["ephemeral"] == ["true"]
    assert beat["serviceName"] == "mcp-server-knowledge"
    assert beat["ip"] == "10.0.0.12"
    assert beat["port"] == 18081
    assert beat["ephemeral"] is True
    mcp_metadata = json.loads(beat["metadata"]["mcp"])
    assert mcp_metadata["tools"][0]["name"] == "knowledge.search"


def test_lifecycle_registers_and_deregisters_once():
    calls = []

    class FakeRegistrar:
        def register_instance(self, registration):
            calls.append(
                ("register", registration.service_name, registration.ip, registration.port)
            )
            return "registered"

        def deregister_instance(self, service_name, ip, port):
            calls.append(("deregister", service_name, ip, port))
            return "deregistered"

        def send_heartbeat(self, registration):
            calls.append(("heartbeat", registration.service_name))
            return "ok"

    registration = McpServerRegistration(
        service_name="mcp-server-knowledge",
        ip="10.0.0.12",
        port=18081,
        metadata=knowledge_search_metadata(),
    )
    lifecycle = McpServerNacosLifecycle(FakeRegistrar(), registration)

    assert lifecycle.start() == "registered"
    assert lifecycle.start() is None
    assert lifecycle.registered is True
    assert lifecycle.stop() == "deregistered"
    assert lifecycle.stop() is None
    assert lifecycle.registered is False
    assert calls == [
        ("register", "mcp-server-knowledge", "10.0.0.12", 18081),
        ("deregister", "mcp-server-knowledge", "10.0.0.12", 18081),
    ]


def test_lifecycle_context_manager_deregisters_after_error():
    calls = []

    class FakeRegistrar:
        def register_instance(self, registration):
            calls.append(("register", registration.service_name))
            return "registered"

        def deregister_instance(self, service_name, ip, port):
            calls.append(("deregister", service_name))
            return "deregistered"

        def send_heartbeat(self, registration):
            calls.append(("heartbeat", registration.service_name))
            return "ok"

    registration = McpServerRegistration(
        service_name="mcp-server-knowledge",
        ip="10.0.0.12",
        port=18081,
        metadata=knowledge_search_metadata(),
    )
    lifecycle = McpServerNacosLifecycle(FakeRegistrar(), registration)

    try:
        with lifecycle:
            raise RuntimeError("server failed")
    except RuntimeError:
        pass

    assert lifecycle.registered is False
    assert calls == [
        ("register", "mcp-server-knowledge"),
        ("deregister", "mcp-server-knowledge"),
    ]


def test_lifecycle_sends_heartbeat_for_ephemeral_registration():
    calls = []

    class FakeRegistrar:
        def register_instance(self, registration):
            calls.append(("register", registration.service_name))
            return "registered"

        def deregister_instance(self, service_name, ip, port):
            calls.append(("deregister", service_name))
            return "deregistered"

        def send_heartbeat(self, registration):
            calls.append(("heartbeat", registration.service_name))
            return "ok"

    registration = McpServerRegistration(
        service_name="mcp-server-knowledge",
        ip="10.0.0.12",
        port=18081,
        metadata=knowledge_search_metadata(),
        ephemeral=True,
    )
    lifecycle = McpServerNacosLifecycle(
        FakeRegistrar(),
        registration,
        heartbeat_interval_seconds=60,
    )

    lifecycle.start()
    lifecycle.stop()

    assert calls == [
        ("register", "mcp-server-knowledge"),
        ("heartbeat", "mcp-server-knowledge"),
        ("deregister", "mcp-server-knowledge"),
    ]
