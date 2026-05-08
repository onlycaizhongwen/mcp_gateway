from __future__ import annotations

from collections import defaultdict

from mcp_gateway.domain.models import McpServerInstance, ToolDescriptor


class ToolCatalog:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDescriptor] = {}

    def refresh(self, instances: list[McpServerInstance]) -> None:
        grouped: dict[tuple[str, str, str], list[tuple[McpServerInstance, object]]] = defaultdict(list)

        for instance in instances:
            if not instance.metadata.enabled:
                continue
            for tool in instance.metadata.tools:
                if not tool.enabled:
                    continue
                key = (tool.name, tool.version, instance.metadata.domain)
                grouped[key].append((instance, tool))

        next_tools: dict[str, ToolDescriptor] = {}
        for (name, version, domain), providers in grouped.items():
            first_instance, first_tool = providers[0]
            healthy_instances = [instance for instance, _ in providers if instance.healthy]
            descriptor = ToolDescriptor(
                name=name,
                version=version,
                domain=domain,
                description=first_tool.description,
                input_schema_ref=first_tool.input_schema_ref,
                output_schema_ref=first_tool.output_schema_ref,
                read_only=first_tool.read_only,
                destructive=first_tool.destructive,
                idempotent=first_tool.idempotent,
                enabled=first_tool.enabled,
                provider_instances=healthy_instances,
                conflict=len({instance.service_name for instance, _ in providers}) > 1
                and len(healthy_instances) == 0,
            )
            next_tools[f"{name}:{version}"] = descriptor

        self._tools = next_tools

    def list_tools(self) -> list[ToolDescriptor]:
        return sorted(self._tools.values(), key=lambda tool: tool.name)

    def get_tool(self, name: str, version: str | None = None) -> ToolDescriptor | None:
        if version:
            return self._tools.get(f"{name}:{version}")

        matches = [tool for tool in self._tools.values() if tool.name == name]
        if not matches:
            return None
        return sorted(matches, key=lambda tool: tool.version, reverse=True)[0]
