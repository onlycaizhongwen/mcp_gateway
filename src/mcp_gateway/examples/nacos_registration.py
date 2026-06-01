from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from types import TracebackType
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
    ephemeral: bool = False


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

    def send_heartbeat(self, registration: McpServerRegistration) -> str:
        payload: dict[str, Any] = {
            "serviceName": registration.service_name,
            "groupName": self._config.group,
            "ip": registration.ip,
            "port": registration.port,
            "ephemeral": str(registration.ephemeral).lower(),
            "beat": json.dumps(
                {
                    "serviceName": registration.service_name,
                    "ip": registration.ip,
                    "port": registration.port,
                    "weight": registration.weight,
                    "ephemeral": registration.ephemeral,
                    "scheduled": True,
                    "metadata": {"mcp": json.dumps(registration.metadata, ensure_ascii=False)},
                },
                ensure_ascii=False,
            ),
        }
        if self._config.namespace:
            payload["namespaceId"] = self._config.namespace
        return self._put_form("/nacos/v1/ns/instance/beat", payload)

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
            "metadata": json.dumps(
                {"mcp": json.dumps(registration.metadata, ensure_ascii=False)},
                ensure_ascii=False,
            ),
        }
        if self._config.namespace:
            payload["namespaceId"] = self._config.namespace
        return payload

    def _post_form(self, path: str, payload: dict[str, Any]) -> str:
        return self._request_form(path, payload, method="POST")

    def _put_form(self, path: str, payload: dict[str, Any]) -> str:
        return self._request_form(path, payload, method="PUT")

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


class McpServerNacosLifecycle:
    """Register an MCP Server on startup and deregister it on shutdown."""

    def __init__(
        self,
        registrar: NacosMcpServerRegistrar,
        registration: McpServerRegistration,
        *,
        deregister_on_exit: bool = True,
        ignore_deregister_errors: bool = False,
        heartbeat_interval_seconds: float | None = None,
        ignore_heartbeat_errors: bool = True,
    ) -> None:
        self._registrar = registrar
        self._registration = registration
        self._deregister_on_exit = deregister_on_exit
        self._ignore_deregister_errors = ignore_deregister_errors
        self._heartbeat_interval_seconds = heartbeat_interval_seconds
        self._ignore_heartbeat_errors = ignore_heartbeat_errors
        self._registered = False
        self._stop_heartbeat = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None

    @property
    def registered(self) -> bool:
        return self._registered

    def start(self) -> str | None:
        if self._registered:
            return None
        result = self._registrar.register_instance(self._registration)
        self._registered = True
        try:
            self._start_heartbeat_if_needed()
        except Exception:
            self.stop()
            raise
        return result

    def stop(self) -> str | None:
        self._stop_heartbeat_thread()
        if not self._registered or not self._deregister_on_exit:
            return None
        try:
            result = self._registrar.deregister_instance(
                self._registration.service_name,
                self._registration.ip,
                self._registration.port,
            )
        except Exception:
            if not self._ignore_deregister_errors:
                raise
            self._registered = False
            return None
        self._registered = False
        return result

    def _start_heartbeat_if_needed(self) -> None:
        if not self._registration.ephemeral or not self._heartbeat_interval_seconds:
            return
        self._stop_heartbeat.clear()
        self._send_heartbeat()
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            name=f"nacos-heartbeat-{self._registration.service_name}",
            daemon=True,
        )
        self._heartbeat_thread.start()

    def _heartbeat_loop(self) -> None:
        while not self._stop_heartbeat.wait(self._heartbeat_interval_seconds):
            self._send_heartbeat()

    def _send_heartbeat(self) -> None:
        try:
            self._registrar.send_heartbeat(self._registration)
        except Exception:
            if not self._ignore_heartbeat_errors:
                raise

    def _stop_heartbeat_thread(self) -> None:
        self._stop_heartbeat.set()
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=1)
        self._heartbeat_thread = None

    def __enter__(self) -> "McpServerNacosLifecycle":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        self.stop()
        return False


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
