from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Protocol

from mcp_gateway.config.gateway_config import GatewayConfig, RateLimitConfig, RedisStateConfig
from mcp_gateway.domain.errors import ErrorCode, GatewayError
from mcp_gateway.policy.auth_context import AuthContext


@dataclass
class TokenBucket:
    tokens: float
    updated_at: float


class RateLimiterStore(Protocol):
    def allow(
        self,
        bucket_key: str,
        qps: int,
        burst: int,
        now: float,
    ) -> bool:
        """Consume one token and return whether the request is allowed."""

    def snapshot(self) -> dict[str, dict[str, float]]:
        """Return a diagnostic snapshot when the backend supports it."""


class InMemoryRateLimiterStore:
    def __init__(self) -> None:
        self._buckets: dict[str, TokenBucket] = {}

    def allow(self, bucket_key: str, qps: int, burst: int, now: float) -> bool:
        bucket = self._buckets.get(bucket_key)
        if bucket is None:
            bucket = TokenBucket(tokens=float(burst), updated_at=now)
            self._buckets[bucket_key] = bucket

        elapsed = max(0.0, now - bucket.updated_at)
        bucket.tokens = min(float(burst), bucket.tokens + elapsed * float(qps))
        bucket.updated_at = now

        if bucket.tokens < 1:
            return False

        bucket.tokens -= 1
        return True

    def snapshot(self) -> dict[str, dict[str, float]]:
        return {
            key: {"tokens": bucket.tokens, "updatedAt": bucket.updated_at}
            for key, bucket in self._buckets.items()
        }


class RedisRateLimiterStore:
    _SCRIPT = """
local key = KEYS[1]
local qps = tonumber(ARGV[1])
local burst = tonumber(ARGV[2])
local ttl_ms = tonumber(ARGV[3])
local server_time = redis.call('TIME')
local now = tonumber(server_time[1]) + tonumber(server_time[2]) / 1000000

local state = redis.call('HMGET', key, 'tokens', 'updated_at')
local tokens = tonumber(state[1])
local updated_at = tonumber(state[2])

if tokens == nil then
  tokens = burst
  updated_at = now
end

local elapsed = math.max(0, now - updated_at)
tokens = math.min(burst, tokens + elapsed * qps)
updated_at = now

local allowed = 0
if tokens >= 1 then
  tokens = tokens - 1
  allowed = 1
end

redis.call('HMSET', key, 'tokens', tokens, 'updated_at', updated_at)
redis.call('PEXPIRE', key, ttl_ms)
return allowed
"""

    def __init__(
        self,
        config: RedisStateConfig,
        redis_client: object | None = None,
    ) -> None:
        self._key_prefix = config.key_prefix.rstrip(":")
        if redis_client is None:
            from redis import Redis

            redis_client = Redis.from_url(
                config.url,
                socket_timeout=config.socket_timeout_seconds,
                socket_connect_timeout=config.socket_timeout_seconds,
                decode_responses=True,
            )
        self._redis = redis_client

    def allow(self, bucket_key: str, qps: int, burst: int, now: float) -> bool:
        key = f"{self._key_prefix}:rate-limit:{bucket_key}"
        ttl_ms = max(1000, int(((burst / max(qps, 1)) + 60) * 1000))
        allowed = self._redis.eval(self._SCRIPT, 1, key, qps, burst, ttl_ms)
        return int(allowed) == 1

    def snapshot(self) -> dict[str, dict[str, float]]:
        return {}


def create_rate_limiter_store(config: GatewayConfig | None) -> RateLimiterStore:
    if config is not None and config.state_backend.mode == "redis":
        return RedisRateLimiterStore(config.state_backend.redis)
    return InMemoryRateLimiterStore()


class RateLimiter:
    def __init__(
        self,
        config: GatewayConfig | None = None,
        app_limits: dict[str, RateLimitConfig] | None = None,
        now: Callable[[], float] = time.monotonic,
        store: RateLimiterStore | None = None,
    ) -> None:
        self._now = now
        self._app_limits: dict[str, RateLimitConfig] = app_limits or {}
        if config is not None:
            self._app_limits = {
                app.app_id: app.rate_limit
                for app in config.permissions.apps
                if app.rate_limit is not None
            }
        self._store = store or create_rate_limiter_store(config)

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
        if not self._store.allow(bucket_key, limit.qps, limit.burst, self._now()):
            raise GatewayError(
                ErrorCode.RATE_LIMITED,
                f"App {context.app_id} exceeded rate limit for {tool_name}",
                429,
            )

    def snapshot(self) -> dict[str, dict[str, float]]:
        return self._store.snapshot()
