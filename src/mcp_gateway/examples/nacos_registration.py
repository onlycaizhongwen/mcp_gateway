from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class NacosRegistrationConfig:
    endpoint: str = "http://127.0.0.1:8848"
    namespace: str | None = None
    group: str = "MCP_SERVER_GROUP"
    username: str | None = None
    password: str | None = None
    timeout_seconds: float = 3


@dataclass(frozen=True)
class McpServerRegistration:
    service_name: str
    ip: str
    port: int
    metadata: dict[str, Any]
    weight: int = 100
    enabled: bool = True
    healthy: bool = True
    ephemeral: bool = True


class NacosMcpServerRegistrar:
    def __init__(self, config: NacosRegistrationConfig) -> None:
        self._config = config
        self._access_token: str | None = None

    def register_instance(self, registration: McpServerRegistration) -> str:
        payload = self._build_payload(registration)
        return self._post_form("/nacos/v1/ns/instance", payload)

    def deregister_instance(self, service_name: str, ip: str, port: int) -> str:
        payload: dict[str, Any] = {
            "serviceName": service_name,
            "groupName": self._config.group,
            "ip": ip,
            "port": port,
        }
        if self._config.namespace:
            payload["namespaceId"] = self._config.namespace
        return self._delete_form("/nacos/v1/ns/instance", payload)

    def _build_payload(self, registration: McpServerRegistration) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "serviceName": registration.service_name,
            "groupName": self._config.group,
            "ip": registration.ip,
            "port": registration.port,
            "weight": registration.weight,
            "enabled": str(registration.enabled).lower(),
            "healthy": str(registration.healthy).lower(),
            "ephemeral": str(registration.ephemeral).lower(),
            "metadata": json.dumps(registration.metadata, ensure_ascii=False),
        }
        if self._config.namespace:
            payload["namespaceId"] = self._config.namespace
        return payload

    def _post_form(self, path: str, payload: dict[str, Any]) -> str:
        return self._request_form(path, payload, method="POST")

    def _delete_form(self, path: str, payload: dict[str, Any]) -> str:
        return self._request_form(path, payload, method="DELETE")

    def _request_form(self, path: str, payload: dict[str, Any], method: str) -> str:
        endpoint = self._config.endpoint.rstrip("/")
        body = dict(payload)
        token = self._get_access_token()
        if token:
            body["accessToken"] = token
        request = Request(
            f"{endpoint}{path}",
            data=urlencode(body).encode("utf-8"),
            method=method,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(request, timeout=self._config.timeout_seconds) as response:
            return response.read().decode("utf-8")

    def _get_access_token(self) -> str | None:
        if not self._config.username or not self._config.password:
            return None
        if self._access_token:
            return self._access_token

        endpoint = self._config.endpoint.rstrip("/")
        body = urlencode(
            {"username": self._config.username, "password": self._config.password}
        ).encode("utf-8")
        request = Request(
            f"{endpoint}/nacos/v1/auth/login",
            data=body,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(request, timeout=self._config.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self._access_token = payload.get("accessToken")
        return self._access_token


def knowledge_search_metadata() -> dict[str, Any]:
    return {
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
        "labels": ["example", "knowledge"],
        "tools": [
            {
                "name": "knowledge.search",
                "version": "1.0.0",
                "description": "Search enterprise knowledge base",
                "inputSchemaRef": "nacos://mcp-schemas/knowledge.search/1.0.0/input",
                "outputSchemaRef": "nacos://mcp-schemas/knowledge.search/1.0.0/output",
                "readOnly": True,
                "destructive": False,
                "idempotent": True,
                "enabled": True,
            }
        ],
    }
