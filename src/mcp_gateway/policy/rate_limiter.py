from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from mcp_gateway.config.gateway_config import GatewayConfig, RateLimitConfig
from mcp_gateway.domain.errors import ErrorCode, GatewayError
from mcp_gateway.policy.auth_context import AuthContext


@dataclass
class TokenBucket:
    tokens: float
    updated_at: float


class RateLimiter:
    def __init__(
        self,
        config: GatewayConfig | None = None,
        app_limits: dict[str, RateLimitConfig] | None = None,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self._now = now
        self._app_limits: dict[str, RateLimitConfig] = app_limits or {}
        if config is not None:
            self._app_limits = {
                app.app_id: app.rate_limit
                for app in config.permissions.apps
                if app.rate_limit is not None
            }
        self._buckets: dict[str, TokenBucket] = {}

    def ensure_allowed(self, context: AuthContext, tool_name: str) -> None:
        if not context.app_id:
            return

        limit = self._app_limits.get(context.app_id)
        if limit is None or limit.qps is None or limit.burst is None:
            return
        if limit.qps <= 0 or limit.burst <= 0:
            raise GatewayError(
                ErrorCode.RATE_LIMITED,
                f"App {context.app_id} exceeded rate limit for {tool_name}",
                429,
            )

        bucket_key = f"{context.app_id}:{context.tenant_id or '-'}:{tool_name}"
        now = self._now()
        bucket = self._buckets.get(bucket_key)
        if bucket is None:
            bucket = TokenBucket(tokens=float(limit.burst), updated_at=now)
            self._buckets[bucket_key] = bucket

        elapsed = max(0.0, now - bucket.updated_at)
        bucket.tokens = min(float(limit.burst), bucket.tokens + elapsed * float(limit.qps))
        bucket.updated_at = now

        if bucket.tokens < 1:
            raise GatewayError(
                ErrorCode.RATE_LIMITED,
                f"App {context.app_id} exceeded rate limit for {tool_name}",
                429,
            )

        bucket.tokens -= 1

    def snapshot(self) -> dict[str, dict[str, float]]:
        return {
            key: {"tokens": bucket.tokens, "updatedAt": bucket.updated_at}
            for key, bucket in self._buckets.items()
        }
