from __future__ import annotations

from redis import Redis

from mcp_gateway.config.gateway_config import RedisStateConfig
from mcp_gateway.domain.errors import GatewayError
from mcp_gateway.policy.auth_context import AuthContext
from mcp_gateway.policy.rate_limiter import RateLimiter, RedisRateLimiterStore
from mcp_gateway.config.gateway_config import RateLimitConfig
from mcp_gateway.routing.circuit_breaker import CircuitBreaker, RedisCircuitBreakerStore


def main() -> None:
    redis_config = RedisStateConfig(
        url="redis://127.0.0.1:6379/0",
        key_prefix="mcp-gateway-smoke",
    )
    redis_client = Redis.from_url(redis_config.url, decode_responses=True)
    for key in redis_client.scan_iter(f"{redis_config.key_prefix}:*"):
        redis_client.delete(key)

    rate_store = RedisRateLimiterStore(redis_config, redis_client=redis_client)
    limiter_a = RateLimiter(
        app_limits={"internal-ai-agent": RateLimitConfig(qps=1, burst=1)},
        store=rate_store,
    )
    limiter_b = RateLimiter(
        app_limits={"internal-ai-agent": RateLimitConfig(qps=1, burst=1)},
        store=rate_store,
    )
    context = AuthContext(app_id="internal-ai-agent", tenant_id="tenant-a")
    limiter_a.ensure_allowed(context, "knowledge.search")
    try:
        limiter_b.ensure_allowed(context, "knowledge.search")
    except GatewayError:
        print("rate-limit shared state: ok")
    else:
        raise RuntimeError("rate limiter did not share Redis bucket")

    breaker_store = RedisCircuitBreakerStore(redis_config, redis_client=redis_client)
    breaker_a = CircuitBreaker(
        failure_threshold=2,
        recovery_seconds=30,
        store=breaker_store,
    )
    breaker_b = CircuitBreaker(
        failure_threshold=2,
        recovery_seconds=30,
        store=breaker_store,
    )
    breaker_a.record_failure("mcp-server-1")
    if not breaker_b.can_call("mcp-server-1"):
        raise RuntimeError("circuit breaker opened before threshold")
    breaker_b.record_failure("mcp-server-1")
    if breaker_a.can_call("mcp-server-1"):
        raise RuntimeError("circuit breaker did not share Redis open state")
    print("circuit-breaker shared state: ok")


if __name__ == "__main__":
    main()
