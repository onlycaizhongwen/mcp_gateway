import json
from urllib.parse import parse_qs

from mcp_gateway.examples.nacos_schema_config import (
    NacosSchemaConfig,
    NacosSchemaPublisher,
    schema_ref_to_data_id,
)


def test_schema_ref_to_data_id():
    assert (
        schema_ref_to_data_id("nacos://mcp-schemas/knowledge.search/1.0.0/input")
        == "mcp-schemas__knowledge.search__1.0.0__input.json"
    )


def test_nacos_schema_publisher_posts_sample_schema(monkeypatch):
    requests = []

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b"true"

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        return FakeResponse()

    monkeypatch.setattr("mcp_gateway.examples.nacos_schema_config.urlopen", fake_urlopen)
    publisher = NacosSchemaPublisher(
        NacosSchemaConfig(
            endpoint="http://127.0.0.1:8848",
            namespace="dev",
            group="MCP_SCHEMA_GROUP",
            timeout_seconds=2,
        )
    )

    publisher.publish_schema(
        "mcp-schemas__knowledge.search__1.0.0__input.json",
        {"type": "object", "required": ["query"]},
    )

    request, timeout = requests[0]
    body = parse_qs(request.data.decode("utf-8"))
    assert timeout == 2
    assert request.full_url == "http://127.0.0.1:8848/nacos/v1/cs/configs"
    assert body["dataId"] == ["mcp-schemas__knowledge.search__1.0.0__input.json"]
    assert body["group"] == ["MCP_SCHEMA_GROUP"]
    assert body["tenant"] == ["dev"]
    assert body["type"] == ["json"]
    assert json.loads(body["content"][0])["required"] == ["query"]


def test_nacos_schema_publisher_posts_access_token(monkeypatch):
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
        return FakeResponse(b"true")

    monkeypatch.setattr("mcp_gateway.examples.nacos_schema_config.urlopen", fake_urlopen)
    publisher = NacosSchemaPublisher(
        NacosSchemaConfig(
            endpoint="http://127.0.0.1:8848",
            username="nacos",
            password="nacos",
        )
    )

    publisher.publish_schema("mcp-schemas__knowledge.search__1.0.0__input.json", {"type": "object"})

    assert len(requests) == 2
    body = parse_qs(requests[1].data.decode("utf-8"))
    assert body["accessToken"] == ["token-a"]
