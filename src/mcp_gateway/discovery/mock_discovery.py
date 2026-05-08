from __future__ import annotations

from mcp_gateway.discovery.metadata_parser import parse_instance
from mcp_gateway.domain.models import McpServerInstance
from mcp_gateway.examples.sample_metadata import SAMPLE_NACOS_INSTANCES


class MockDiscoveryClient:
    def __init__(self, raw_instances: list[dict] | None = None) -> None:
        self._raw_instances = raw_instances or SAMPLE_NACOS_INSTANCES

    def list_instances(self) -> list[McpServerInstance]:
        instances: list[McpServerInstance] = []
        for raw in self._raw_instances:
            try:
                instances.append(parse_instance(raw))
            except Exception:
                # MVP behavior: invalid metadata is skipped. Real adapter should log details.
                continue
        return instances
