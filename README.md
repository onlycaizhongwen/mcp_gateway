# MCP Gateway

MCP Gateway 是一个基于 Python/FastAPI 的 MCP 工具网关 MVP，用于验证 MCP Server 通过 Nacos 注册工具元数据，Gateway 自动发现、聚合 Tool Catalog，并向上游统一暴露工具查询、schema 查询和工具调用入口。

当前版本定位为 **MCP Gateway MVP / Nacos 联调样例版**，适合架构验证、本地演示、测试环境联调和 MCP Tool 接入规范参考。当前版本不建议直接作为生产版本发布。

## 项目定位

本项目解决的核心问题：

- MCP Server 自动注册到 Nacos。
- MCP Gateway 从 Nacos 发现 MCP Server 实例和工具元数据。
- Gateway 聚合知识库、审批、文档等工具目录。
- 上游应用通过统一 HTTP API 查询工具、查询 schema、调用工具。
- Gateway 层统一处理权限、schema 校验、路由、限流、熔断、审计和指标。

核心链路：

```text
上游 AI 应用
  -> MCP Gateway
  -> Tool Catalog / Router / Policy / Observability
  -> Nacos Discovery + Nacos Config
  -> MCP Server
  -> 真实业务系统或 mock 示例
```

## 当前能力

- Python 3.12 + FastAPI Gateway 工程骨架。
- Mock discovery 和 Nacos OpenAPI discovery adapter。
- Tool Catalog 聚合，支持 `knowledge.search`、`approval.create_task`、`document.generate` 三类演示工具。
- 官方 Python MCP SDK Streamable HTTP client adapter。
- Mock MCP client，用于本地无 MCP Server 演示。
- HTTP API：
  - `GET /api/v1/tools`
  - `GET /api/v1/tools/{toolName}/schema`
  - `POST /api/v1/tools/{toolName}/execute`
- Admin API：
  - `GET /api/v1/admin/catalog/status`
  - `POST /api/v1/admin/catalog/refresh`
- YAML 配置加载和基于 `app_id` 的权限校验。
- 可插拔 schema registry，默认内存样例，可选 Nacos Config 后端。
- traceId / requestId 统一响应封装。
- 可插拔审计，默认日志输出，可选 JSONL 文件落地，不记录参数明文。
- Prometheus 文本格式 `/metrics` 指标出口。
- Prometheus 告警规则样例和观测接入说明。
- 可插拔限流，默认内存后端，可选 Redis token bucket 共享状态后端。
- 可插拔熔断，默认内存后端，可选 Redis 共享状态后端。
- 可选主动健康检查。
- Nacos discovery 失败后保留最后一次成功 Catalog 快照。
- 可选定时 Catalog 刷新。
- Python MCP Server Nacos 注册 helper、生命周期封装和 ephemeral 心跳。
- Java MCP Server Nacos 注册 helper 示例，兼容 JDK 8。

## 目录说明

```text
config/                         Gateway 配置样例
deploy/prometheus/              Prometheus 告警规则样例
docs/codex/v1/                  需求、设计、计划、交付、追踪和运维文档
examples/                       本地联调脚本和 mock MCP Server
examples/java/nacos-registration/
                                Java MCP Server Nacos 注册 helper 示例
src/mcp_gateway/                Gateway 主代码
tests/                          单元测试和示例契约测试
docker-compose.nacos.yml        本地 Nacos compose
docker-compose.redis.yml        本地 Redis compose
```

## 快速开始

安装依赖：

```powershell
python -m pip install -e ".[dev]"
```

启动 Gateway：

```powershell
python -m uvicorn mcp_gateway.main:app --reload
```

打开 API 文档：

```text
http://127.0.0.1:8000/docs
```

使用自定义配置文件：

```powershell
$env:MCP_GATEWAY_CONFIG="D:\path\to\mcp-gateway.yaml"
python -m uvicorn mcp_gateway.main:app --reload
```

## 示例调用

查询工具列表：

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/v1/tools
```

查询工具 schema：

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/v1/tools/knowledge.search/schema
```

调用知识库搜索：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/tools/knowledge.search/execute `
  -ContentType "application/json" `
  -Body '{"tenant_id":"tenant-a","app_id":"internal-ai-agent","arguments":{"query":"年假政策","top_k":1}}'
```

查看 Catalog 状态：

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri http://127.0.0.1:8000/api/v1/admin/catalog/status `
  -Headers @{"x-app-id"="internal-ai-agent"}
```

查看 Prometheus 指标：

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/metrics
```

## Nacos 联调

启动本地 Nacos：

```powershell
docker compose -f docker-compose.nacos.yml up -d
```

启动示例 MCP Server：

```powershell
python -m uvicorn examples.mock_mcp_server:app --host 127.0.0.1 --port 18081
```

注册示例 MCP Server：

```powershell
python examples/register_mcp_server_to_nacos.py `
  --endpoint http://127.0.0.1:8848 `
  --namespace dev `
  --service-name mcp-server-knowledge `
  --ip 127.0.0.1 `
  --port 18081
```

发布 mock schema 到 Nacos Config：

```powershell
python examples/publish_schemas_to_nacos.py `
  --endpoint http://127.0.0.1:8848 `
  --group MCP_SCHEMA_GROUP
```

使用本地 Nacos 配置启动 Gateway：

```powershell
$env:MCP_GATEWAY_CONFIG="D:\czw_ai_project\mcp_gateway\config\mcp-gateway-nacos-local.yaml"
python -m uvicorn mcp_gateway.main:app --host 127.0.0.1 --port 18080
```

更多说明见：

- `docs/codex/v1/designs/mcp-gateway-nacos-integration-guide.md`
- `docs/codex/v1/designs/mcp-server-nacos-registration-template.json`

## MCP Server 注册 Helper

Python helper：

- `src/mcp_gateway/examples/nacos_registration.py`
- `examples/register_mcp_server_to_nacos.py`

Python MCP Server 可复用 `McpServerNacosLifecycle`：

```python
from mcp_gateway.examples.nacos_registration import (
    McpServerNacosLifecycle,
    McpServerRegistration,
    NacosMcpServerRegistrar,
    NacosRegistrationConfig,
    knowledge_search_metadata,
)

registrar = NacosMcpServerRegistrar(
    NacosRegistrationConfig(endpoint="http://127.0.0.1:8848")
)
lifecycle = McpServerNacosLifecycle(
    registrar,
    McpServerRegistration(
        service_name="mcp-server-knowledge",
        ip="127.0.0.1",
        port=18081,
        metadata=knowledge_search_metadata(),
        ephemeral=True,
    ),
    heartbeat_interval_seconds=5,
)

lifecycle.start()
lifecycle.stop()
```

Java helper：

```text
examples/java/nacos-registration/
```

Java 示例包含注册、注销、鉴权 token、ephemeral 心跳、`AutoCloseable` 生命周期封装和 `knowledge.search` metadata 示例。

## 配置说明

主配置文件：

```text
config/mcp-gateway.yaml
```

启用真实 Nacos discovery：

```yaml
discovery:
  mode: nacos
nacos:
  enabled: true
  endpoint: http://nacos.example.com:8848
  namespace: dev
  group: MCP_SERVER_GROUP
  service_names:
    - mcp-server-knowledge
```

启用真实 MCP Server 调用：

```yaml
mcp_client:
  mode: streamable-http
  timeout_seconds: 10
```

启用 Nacos Config schema registry：

```yaml
schema_registry:
  mode: nacos_config
  nacos_config:
    group: MCP_SCHEMA_GROUP
```

启用 Redis 共享治理状态：

```yaml
state_backend:
  mode: redis
  redis:
    url: redis://127.0.0.1:6379/0
    key_prefix: mcp-gateway
    socket_timeout_seconds: 1
```

限流配置：

```yaml
permissions:
  apps:
    - app_id: internal-ai-agent
      allowed_tools:
        - knowledge.search
      rate_limit:
        qps: 20
        burst: 50
```

熔断配置：

```yaml
circuit_breaker:
  enabled: true
  failure_threshold: 3
  recovery_seconds: 30
```

审计文件落地：

```yaml
audit:
  mode: file
  file:
    path: logs/mcp-gateway-audit.jsonl
```

## Redis 治理联调

启动本地 Redis：

```powershell
docker compose -f docker-compose.redis.yml up -d
```

执行共享治理 smoke：

```powershell
python examples/redis_governance_smoke.py
```

当前本地验证结果：真实 Redis 中限流桶和熔断打开状态均可跨两个 Gateway 治理对象共享。

## 可观测性

已提供：

- `/metrics` Prometheus 文本格式指标。
- `deploy/prometheus/mcp-gateway-alerts.yml` 告警规则样例。
- JSONL 审计文件落地能力。
- traceId / requestId 透传。

接入说明：

```text
docs/codex/v1/operations/mcp-gateway-observability.md
```

## 测试

执行全量测试：

```powershell
python -m pytest
```

当前验证结果：

```text
81 passed
```

覆盖范围包括 API、权限、schema、Nacos discovery、Nacos Config、MCP SDK client、审计、metrics、Redis 限流、Redis 熔断、健康检查、注册 helper、Java helper 示例和文档契约。

## 核心文档

- 需求文档：`docs/codex/v1/requirements/mcp-gateway-nacos-discovery-requirements.md`
- 技术设计：`docs/codex/v1/designs/mcp-gateway-nacos-discovery-design.md`
- HTML 设计：`docs/codex/v1/designs/mcp-gateway-nacos-discovery-design.html`
- 执行计划：`docs/codex/v1/plans/mcp-gateway-nacos-discovery-plan.md`
- Trace 审查：`docs/codex/v1/trace/mcp-gateway-nacos-discovery-trace.md`
- MVP 交付说明：`docs/codex/v1/delivery/mcp-gateway-mvp-delivery.md`
- Nacos 联调说明：`docs/codex/v1/designs/mcp-gateway-nacos-integration-guide.md`
- 观测接入说明：`docs/codex/v1/operations/mcp-gateway-observability.md`

## 交付状态

当前已完成：

- MCP Gateway MVP 主链路。
- 本地 Docker Nacos 注册、发现、Nacos Config schema 和调用联调。
- 本地 Docker Redis 限流、熔断共享状态 smoke。
- Python/Java MCP Server 注册 helper 示例。
- Prometheus 指标出口、告警规则样例和观测接入说明。

仍需在真实环境完成：

- 公司生产 Nacos 环境参数验证。
- 将 Python 或 Java 注册生命周期和 ephemeral 心跳 helper 嵌入真实 MCP Server。
- 接入真实知识库、审批、文档业务系统。
- 接入统一鉴权或权限中心。
- 对 Redis 限流、熔断共享状态做生产压测，并按公司指标平台校准告警阈值。
- 接入公司审计中心/日志平台和指标平台采集配置。

## 已知限制

- 默认配置使用 mock discovery、mock MCP client 和内存 schema registry。
- 三类 Tool 当前为演示链路，不包含真实业务逻辑。
- 当前已通过本地 Docker Nacos 验证，尚未经过公司测试/生产 Nacos 环境验证。
- 当前没有 Nacos watch 推送，仅支持手动 refresh 和可选定时 refresh。
- 当前 metrics 耗时指标为 sum/count，生产 P95/P99 需要升级 histogram。
