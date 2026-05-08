import pytest

from mcp_gateway.discovery.metadata_parser import parse_instance
from mcp_gateway.domain.errors import GatewayError
from mcp_gateway.examples.sample_metadata import SAMPLE_NACOS_INSTANCES


def test_parse_valid_instance():
    instance = parse_instance(SAMPLE_NACOS_INSTANCES[0])

    assert instance.instance_id == "knowledge-1"
    assert instance.metadata.tools[0].name == "knowledge.search"
    assert instance.metadata.transport == "streamable-http"


def test_parse_invalid_instance_raises_gateway_error():
    invalid = {"service_name": "broken"}

    with pytest.raises(GatewayError):
        parse_instance(invalid)
