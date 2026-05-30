from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

from mcp_gateway.examples.sample_schemas import SAMPLE_SCHEMAS


@dataclass(frozen=True)
class NacosSchemaConfig:
    endpoint: str = "http://127.0.0.1:8848"
    namespace: str | None = None
    group: str = "MCP_SCHEMA_GROUP"
    username: str | None = None
    password: str | None = None
    timeout_seconds: float = 3


class NacosSchemaPublisher:
    def __init__(self, config: NacosSchemaConfig) -> None:
        self._config = config
        self._access_token: str | None = None

    def publish_sample_schemas(self) -> list[str]:
        data_ids: list[str] = []
        for schema_ref, schema in SAMPLE_SCHEMAS.items():
            data_id = schema_ref_to_data_id(schema_ref)
            self.publish_schema(data_id, schema)
            data_ids.append(data_id)
        return data_ids

    def publish_schema(self, data_id: str, schema: dict[str, Any]) -> None:
        form: dict[str, Any] = {
            "dataId": data_id,
            "group": self._config.group,
            "content": json.dumps(schema, ensure_ascii=False),
            "type": "json",
        }
        if self._config.namespace:
            form["tenant"] = self._config.namespace
        token = self._get_access_token()
        if token:
            form["accessToken"] = token

        request = Request(
            f"{self._endpoint()}/nacos/v1/cs/configs",
            data=urlencode(form, quote_via=quote).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urlopen(request, timeout=self._config.timeout_seconds) as response:
            body = response.read().decode("utf-8")
        if body.strip().lower() != "true":
            raise RuntimeError(f"Nacos rejected schema config dataId={data_id}: {body}")

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
        with urlopen(request, timeout=self._config.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self._access_token = payload.get("accessToken")
        return self._access_token

    def _endpoint(self) -> str:
        return self._config.endpoint.rstrip("/")


def schema_ref_to_data_id(schema_ref: str) -> str:
    parsed = urlparse(schema_ref)
    if parsed.scheme != "nacos" or not parsed.netloc or not parsed.path.strip("/"):
        raise ValueError(f"Unsupported Nacos schema ref: {schema_ref}")
    path_parts = parsed.path.strip("/").split("/")
    return "__".join([parsed.netloc, *path_parts]) + ".json"
