from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Protocol

from mcp_gateway.config.gateway_config import RedisStateConfig


@dataclass
class CircuitBreakerState:
    failure_count: int = 0
    opened_at: float | None = None


class CircuitBreakerStore(Protocol):
    def can_call(self, instance_id: str, recovery_seconds: float, now: float) -> bool:
        """Return whether the instance is closed or ready for half-open probing."""

    def record_success(self, instance_id: str) -> None:
        """Clear breaker state after a successful call."""

    def record_failure(
        self,
        instance_id: str,
        failure_threshold: int,
        recovery_seconds: float,
        now: float,
    ) -> None:
        """Record a failure and open the breaker when threshold is reached."""

    def snapshot(
        self,
        recovery_seconds: float,
        now: float,
    ) -> dict[str, dict[str, float | int | bool | None]]:
        """Return diagnostic breaker state."""


class InMemoryCircuitBreakerStore:
    def __init__(self) -> None:
        self._states: dict[str, CircuitBreakerState] = {}

    def can_call(self, instance_id: str, recovery_seconds: float, now: float) -> bool:
        state = self._states.get(instance_id)
        if state is None or state.opened_at is None:
            return True

        return now - state.opened_at >= recovery_seconds

    def record_success(self, instance_id: str) -> None:
        self._states.pop(instance_id, None)

    def record_failure(
        self,
        instance_id: str,
        failure_threshold: int,
        recovery_seconds: float,
        now: float,
    ) -> None:
        state = self._states.setdefault(instance_id, CircuitBreakerState())
        state.failure_count += 1
        if state.failure_count >= failure_threshold:
            state.opened_at = now

    def snapshot(
        self,
        recovery_seconds: float,
        now: float,
    ) -> dict[str, dict[str, float | int | bool | None]]:
        return {
            instance_id: {
                "failureCount": state.failure_count,
                "openedAt": state.opened_at,
                "open": state.opened_at is not None
                and now - state.opened_at < recovery_seconds,
            }
            for instance_id, state in self._states.items()
        }


class RedisCircuitBreakerStore:
    _FAILURE_SCRIPT = """
local key = KEYS[1]
local threshold = tonumber(ARGV[1])
local ttl_ms = tonumber(ARGV[2])
local server_time = redis.call('TIME')
local now = tonumber(server_time[1]) + tonumber(server_time[2]) / 1000000

local failure_count = redis.call('HINCRBY', key, 'failure_count', 1)
if failure_count >= threshold then
  redis.call('HSET', key, 'opened_at', now)
end
redis.call('PEXPIRE', key, ttl_ms)
return failure_count
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

    def _key(self, instance_id: str) -> str:
        return f"{self._key_prefix}:circuit-breaker:{instance_id}"

    def can_call(self, instance_id: str, recovery_seconds: float, now: float) -> bool:
        opened_at = self._redis.hget(self._key(instance_id), "opened_at")
        if opened_at is None:
            return True
        return now - float(opened_at) >= recovery_seconds

    def record_success(self, instance_id: str) -> None:
        self._redis.delete(self._key(instance_id))

    def record_failure(
        self,
        instance_id: str,
        failure_threshold: int,
        recovery_seconds: float,
        now: float,
    ) -> None:
        ttl_ms = max(1000, int((recovery_seconds + 3600) * 1000))
        self._redis.eval(
            self._FAILURE_SCRIPT,
            1,
            self._key(instance_id),
            failure_threshold,
            ttl_ms,
        )

    def snapshot(
        self,
        recovery_seconds: float,
        now: float,
    ) -> dict[str, dict[str, float | int | bool | None]]:
        return {}


class CircuitBreaker:
    def __init__(
        self,
        enabled: bool = True,
        failure_threshold: int = 3,
        recovery_seconds: float = 30,
        now: Callable[[], float] = time.monotonic,
        store: CircuitBreakerStore | None = None,
    ) -> None:
        self._enabled = enabled
        self._failure_threshold = max(1, failure_threshold)
        self._recovery_seconds = max(0, recovery_seconds)
        self._now = now
        self._store = store or InMemoryCircuitBreakerStore()

    def can_call(self, instance_id: str) -> bool:
        if not self._enabled:
            return True

        return self._store.can_call(instance_id, self._recovery_seconds, self._now())

    def record_success(self, instance_id: str) -> None:
        if not self._enabled:
            return
        self._store.record_success(instance_id)

    def record_failure(self, instance_id: str) -> None:
        if not self._enabled:
            return

        self._store.record_failure(
            instance_id,
            self._failure_threshold,
            self._recovery_seconds,
            self._now(),
        )

    def snapshot(self) -> dict[str, dict[str, float | int | bool | None]]:
        return self._store.snapshot(self._recovery_seconds, self._now())


def create_circuit_breaker_store(
    mode: str = "memory",
    redis_config: RedisStateConfig | None = None,
) -> CircuitBreakerStore:
    if mode == "redis":
        return RedisCircuitBreakerStore(redis_config or RedisStateConfig())
    return InMemoryCircuitBreakerStore()
