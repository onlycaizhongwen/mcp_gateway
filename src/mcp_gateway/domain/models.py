from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


Transport = Literal["streamable-http", "sse"]


class ToolMetadata(BaseModel):
    name: str
    version: str
    description: str = ""
    input_schema_ref: str = Field(alias="inputSchemaRef")
    output_schema_ref: str = Field(alias="outputSchemaRef")
    read_only: bool = Field(default=False, alias="readOnly")
    destructive: bool = False
    idempotent: bool = False
    enabled: bool = True


class McpServerMetadata(BaseModel):
    metadata_version: str = Field(alias="metadataVersion")
    mcp_protocol_version: str = Field(alias="mcpProtocolVersion")
    transport: Transport
    endpoint: str
    health_path: str = Field(default="/health", alias="healthPath")
    domain: str
    server_version: str = Field(alias="serverVersion")
    tool_set_version: str = Field(alias="toolSetVersion")
    tenant_mode: str = Field(default="shared", alias="tenantMode")
    auth_type: str = Field(default="gateway-token", alias="authType")
    enabled: bool = True
    labels: list[str] = Field(default_factory=list)
    tools: list[ToolMetadata]


class McpServerInstance(BaseModel):
    service_name: str
    instance_id: str
    host: str
    port: int
    weight: int = 100
    healthy: bool = True
    metadata: McpServerMetadata

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}{self.metadata.endpoint}"


class ToolDescriptor(BaseModel):
    name: str
    version: str
    domain: str
    description: str = ""
    input_schema_ref: str
    output_schema_ref: str
    read_only: bool = False
    destructive: bool = False
    idempotent: bool = False
    enabled: bool = True
    provider_instances: list[McpServerInstance] = Field(default_factory=list)
    conflict: bool = False


class ToolRoute(BaseModel):
    tool_name: str
    version: str
    tenant_id: str | None = None
    selected_instance: McpServerInstance
    route_reason: str


class ToolCallRequest(BaseModel):
    arguments: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str | None = None
    app_id: str | None = None
    user: dict[str, Any] | None = None
    trace_id: str | None = None
    request_id: str | None = None
