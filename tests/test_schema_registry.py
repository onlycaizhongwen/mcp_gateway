import pytest

from mcp_gateway.domain.errors import GatewayError
from mcp_gateway.schema.schema_registry import SchemaRegistry


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
