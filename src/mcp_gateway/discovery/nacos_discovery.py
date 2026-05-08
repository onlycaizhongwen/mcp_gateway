from __future__ import annotations

import json
import logging
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from mcp_gateway.config.gateway_config import NacosConfig
from mcp_gateway.discovery.metadata_parser import parse_instance
from mcp_gateway.domain.models import McpServerInstance


logger = logging.getLogger(__name__)


class NacosDiscoveryClient:
    """Small Nacos OpenAPI adapter.

    It is intentionally narrow for the MVP: list configured service names and map
    Nacos hosts to the gateway's internal MCP server instance model.
    """

    def __init__(self, config: NacosConfig) -> None:
        self._config = config
        self._access_token: str | None = None

    def list_instances(self) -> list[McpServerInstance]:
        instances: list[McpServerInstance] = []
        for service_name in self._config.service_names:
            for host in self._list_service_hosts(service_name):
                raw = self._to_raw_instance(service_name, host)
                try:
                    instances.append(parse_instance(raw))
                except Exception as exc:
                    logger.warning(
                        "skip invalid MCP metadata service=%s instance=%s error=%s",
                        service_name,
                        raw.get("instance_id"),
                        exc,
                    )
                    continue
        return instances

    def _list_service_hosts(self, service_name: str) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "serviceName": service_name,
            "groupName": self._config.group,
            "healthyOnly": "false",
        }
        if self._config.namespace:
            params["namespaceId"] = self._config.namespace

        data = self._get_json("/nacos/v1/ns/instance/list", params)
        return data.get("hosts", [])

    def _get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        endpoint = self._config.endpoint.rstrip("/")
        query = dict(params)
        token = self._get_access_token()
        if token:
            query["accessToken"] = token
        url = f"{endpoint}{path}?{urlencode(query)}"
        request = Request(url, method="GET")
        with urlopen(request, timeout=self._config.timeout_seconds) as response:
            body = response.read().decode("utf-8")
        return json.loads(body)

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

    @staticmethod
    def _to_raw_instance(service_name: str, host: dict[str, Any]) -> dict[str, Any]:
        metadata = host.get("metadata") or {}
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        mcp_metadata = metadata.get("mcp")
        if isinstance(mcp_metadata, str):
            metadata = json.loads(mcp_metadata)

        return {
            "service_name": service_name,
            "instance_id": host.get("instanceId") or f"{host.get('ip')}:{host.get('port')}",
            "host": host.get("ip"),
            "port": host.get("port"),
            "weight": int(host.get("weight") or 100),
            "healthy": bool(host.get("healthy", True)),
            "metadata": metadata,
        }
