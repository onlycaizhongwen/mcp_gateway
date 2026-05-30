from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

from mcp_gateway.config.gateway_config import GatewayConfig, NacosConfigStoreConfig
from mcp_gateway.domain.errors import ErrorCode, GatewayError
from mcp_gateway.examples.sample_schemas import SAMPLE_SCHEMAS


class SchemaRegistry:
    def __init__(self, schemas: dict[str, dict[str, Any]] | None = None) -> None:
        self._schemas = schemas or SAMPLE_SCHEMAS

    def get_schema(self, schema_ref: str) -> dict[str, Any]:
        schema = self._schemas.get(schema_ref)
        if schema is None:
            raise GatewayError(
                ErrorCode.TOOL_VALIDATION_FAILED,
                f"Schema not found: {schema_ref}",
                500,
            )
        return schema

    def validate_required(self, schema_ref: str, arguments: dict[str, Any]) -> None:
        schema = self.get_schema(schema_ref)
        required = schema.get("required", [])
        missing = [name for name in required if name not in arguments or arguments[name] is None]
        if missing:
            raise GatewayError(
                ErrorCode.TOOL_VALIDATION_FAILED,
                f"Missing required argument(s): {', '.join(missing)}",
                400,
            )


class NacosConfigSchemaRegistry(SchemaRegistry):
    def __init__(self, config: NacosConfigStoreConfig) -> None:
        super().__init__({})
        self._config = config
        self._cache: dict[str, dict[str, Any]] = {}
        self._access_token: str | None = None

    def get_schema(self, schema_ref: str) -> dict[str, Any]:
        if schema_ref in self._cache:
            return self._cache[schema_ref]

        data_id = self._schema_ref_to_data_id(schema_ref)
        params: dict[str, Any] = {
            "dataId": data_id,
            "group": self._config.group,
        }
        if self._config.namespace:
            params["tenant"] = self._config.namespace

        content = self._get_config(params)
        try:
            schema = json.loads(content)
        except json.JSONDecodeError as exc:
            raise GatewayError(
                ErrorCode.TOOL_VALIDATION_FAILED,
                f"Schema config is not valid JSON: {schema_ref}",
                500,
            ) from exc
        if not isinstance(schema, dict):
            raise GatewayError(
                ErrorCode.TOOL_VALIDATION_FAILED,
                f"Schema config must be a JSON object: {schema_ref}",
                500,
            )

        self._cache[schema_ref] = schema
        return schema

    @staticmethod
    def _schema_ref_to_data_id(schema_ref: str) -> str:
        parsed = urlparse(schema_ref)
        if parsed.scheme != "nacos" or not parsed.netloc or not parsed.path.strip("/"):
            raise GatewayError(
                ErrorCode.TOOL_VALIDATION_FAILED,
                f"Unsupported Nacos schema ref: {schema_ref}",
                500,
            )
        path_parts = parsed.path.strip("/").split("/")
        return "__".join([parsed.netloc, *path_parts]) + ".json"

    def _get_config(self, params: dict[str, Any]) -> str:
        endpoint = self._endpoint()
        query = dict(params)
        token = self._get_access_token()
        if token:
            query["accessToken"] = token
        url = f"{endpoint}/nacos/v1/cs/configs?{urlencode(query, quote_via=quote)}"
        request = Request(url, method="GET")
        with urlopen(request, timeout=self._timeout_seconds()) as response:
            return response.read().decode("utf-8")

    def _get_access_token(self) -> str | None:
        if not self._config.username or not self._config.password:
            return None
        if self._access_token:
            return self._access_token

        body = urlencode(
            {"username": self._config.username, "password": self._config.password}
        ).encode("utf-8")
        request = Request(
            f"{self._endpoint()}/nacos/v1/auth/login",
            data=body,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(request, timeout=self._timeout_seconds()) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self._access_token = payload.get("accessToken")
        return self._access_token

    def _endpoint(self) -> str:
        if not self._config.endpoint:
            raise GatewayError(
                ErrorCode.TOOL_VALIDATION_FAILED,
                "Nacos Config schema registry endpoint is required",
                500,
            )
        return self._config.endpoint.rstrip("/")

    def _timeout_seconds(self) -> float:
        return self._config.timeout_seconds if self._config.timeout_seconds is not None else 3


def create_schema_registry(config: GatewayConfig) -> SchemaRegistry:
    if config.schema_registry.mode == "nacos_config":
        nacos_config = config.schema_registry.nacos_config.model_copy(
            update={
                "endpoint": config.schema_registry.nacos_config.endpoint or config.nacos.endpoint,
                "namespace": (
                    config.schema_registry.nacos_config.namespace
                    if config.schema_registry.nacos_config.namespace is not None
                    else config.nacos.namespace
                ),
                "username": config.schema_registry.nacos_config.username or config.nacos.username,
                "password": config.schema_registry.nacos_config.password or config.nacos.password,
                "timeout_seconds": (
                    config.schema_registry.nacos_config.timeout_seconds
                    if config.schema_registry.nacos_config.timeout_seconds is not None
                    else config.nacos.timeout_seconds
                ),
            }
        )
        return NacosConfigSchemaRegistry(nacos_config)
    return SchemaRegistry()
