import pytest
from fastapi.testclient import TestClient

from mcp_gateway.api.tools import create_tools_router
from mcp_gateway.catalog.tool_catalog import ToolCatalog
from mcp_gateway.client.mock_mcp_client import MockMcpClient
from mcp_gateway.config.gateway_config import RateLimitConfig, RedisStateConfig
from mcp_gateway.discovery.mock_discovery import MockDiscoveryClient
from mcp_gateway.domain.errors import ErrorCode, GatewayError
from mcp_gateway.observability.audit import InMemoryAuditLogger
from mcp_gateway.policy.auth_context import AuthContext
from mcp_gateway.policy.policy_checker import PolicyChecker
from mcp_gateway.policy.rate_limiter import RateLimiter, RedisRateLimiterStore
from mcp_gateway.routing.router_scheduler import RouterScheduler
from mcp_gateway.schema.schema_registry import SchemaRegistry


class ManualClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class FakeRedis:
    def __init__(self) -> None:
        self.buckets = {}
        self.now = 0.0

    def eval(self, _script, _key_count, key, qps, burst, _ttl_ms):
        bucket = self.buckets.get(key)
        if bucket is None:
            bucket = {"tokens": float(burst), "updated_at": self.now}
            self.buckets[key] = bucket

        elapsed = max(0.0, self.now - bucket["updated_at"])
        bucket["tokens"] = min(float(burst), bucket["tokens"] + elapsed * float(qps))
        bucket["updated_at"] = self.now
        if bucket["tokens"] < 1:
            return 0
        bucket["tokens"] -= 1
        return 1


def test_rate_limiter_rejects_when_burst_is_exceeded():
    limiter = RateLimiter(app_limits={"app-a": RateLimitConfig(qps=1, burst=2)})
    context = AuthContext(app_id="app-a", tenant_id="tenant-a")

    limiter.ensure_allowed(context, "knowledge.search")
    limiter.ensure_allowed(context, "knowledge.search")

    with pytest.raises(GatewayError) as exc_info:
        limiter.ensure_allowed(context, "knowledge.search")

    assert exc_info.value.code == ErrorCode.RATE_LIMITED
    assert exc_info.value.status_code == 429


def test_rate_limiter_uses_tenant_scoped_buckets():
    limiter = RateLimiter(app_limits={"app-a": RateLimitConfig(qps=1, burst=1)})

    limiter.ensure_allowed(AuthContext(app_id="app-a", tenant_id="tenant-a"), "knowledge.search")
    limiter.ensure_allowed(AuthContext(app_id="app-a", tenant_id="tenant-b"), "knowledge.search")

    with pytest.raises(GatewayError):
        limiter.ensure_allowed(AuthContext(app_id="app-a", tenant_id="tenant-a"), "knowledge.search")


def test_rate_limiter_refills_tokens_over_time():
    clock = ManualClock()
    limiter = RateLimiter(
        app_limits={"app-a": RateLimitConfig(qps=2, burst=1)},
        now=clock,
    )
    context = AuthContext(app_id="app-a", tenant_id="tenant-a")

    limiter.ensure_allowed(context, "knowledge.search")
    with pytest.raises(GatewayError):
        limiter.ensure_allowed(context, "knowledge.search")

    clock.advance(0.5)
    limiter.ensure_allowed(context, "knowledge.search")


def test_rate_limiter_can_use_redis_store_for_shared_buckets():
    clock = ManualClock()
    fake_redis = FakeRedis()
    store = RedisRateLimiterStore(
        redis_client=fake_redis,
        config=RedisStateConfig(key_prefix="test"),
    )
    limiter_a = RateLimiter(
        app_limits={"app-a": RateLimitConfig(qps=1, burst=1)},
        now=clock,
        store=store,
    )
    limiter_b = RateLimiter(
        app_limits={"app-a": RateLimitConfig(qps=1, burst=1)},
        now=clock,
        store=store,
    )
    context = AuthContext(app_id="app-a", tenant_id="tenant-a")

    limiter_a.ensure_allowed(context, "knowledge.search")
    with pytest.raises(GatewayError):
        limiter_b.ensure_allowed(context, "knowledge.search")

    fake_redis.now += 1
    limiter_b.ensure_allowed(context, "knowledge.search")


def test_execute_tool_returns_429_and_audits_rate_limit():
    catalog = ToolCatalog()
    catalog.refresh(MockDiscoveryClient().list_instances())
    audit_logger = InMemoryAuditLogger()
    from mcp_gateway.main import create_app

    app = create_app()
    app.router.routes.clear()
    app.include_router(
        create_tools_router(
            catalog,
            RouterScheduler(catalog),
            MockMcpClient(),
            PolicyChecker(allowed_tools={"app-a": {"knowledge.search"}}),
            SchemaRegistry(),
            audit_logger,
            rate_limiter=RateLimiter(app_limits={"app-a": RateLimitConfig(qps=1, burst=1)}),
        )
    )
    client = TestClient(app)
    payload = {
        "tenant_id": "tenant-a",
        "app_id": "app-a",
        "arguments": {"query": "policy"},
    }

    assert client.post("/api/v1/tools/knowledge.search/execute", json=payload).status_code == 200
    response = client.post("/api/v1/tools/knowledge.search/execute", json=payload)

    assert response.status_code == 429
    assert response.json()["code"] == "MCP_RATE_LIMITED"
    assert audit_logger.events[-1].result_code == "MCP_RATE_LIMITED"
