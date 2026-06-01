# MCP Gateway MVP 交付说明

版本：v1  
主题：mcp-gateway-nacos-discovery  
交付日期：2026-05-06

## 1. 交付定位

本次交付为 **MCP Gateway MVP / Nacos 联调样例版**。

该版本用于验证企业 AI 升级项目中 MCP 工具层的核心链路：MCP Server 通过 Nacos 注册工具元数据，MCP Gateway 发现、聚合、调度并对上游提供统一工具查询和调用入口。

当前版本适合作为：

- 架构验证版本。
- 本地演示版本。
- Nacos 注册发现联调前置版本。
- MCP Tool 接入规范示例。
- 后续真实知识库、审批、文档 Tool 接入的工程骨架。

当前版本 **不建议直接作为生产版本发布**。

## 2. 交付内容

### 2.1 工程能力

已交付能力：

- Python 3.12 + FastAPI MCP Gateway 工程骨架。
- Mock Discovery 和 Nacos OpenAPI Discovery adapter。
- MCP Server metadata parser。
- Tool Catalog 聚合与查询。
- Router/Scheduler 工具路由。
- 官方 Python MCP SDK Streamable HTTP Client adapter。
- Mock MCP Client。
- 三类演示 Tool：
  - `knowledge.search`
  - `approval.create_task`
  - `document.generate`
- HTTP API：
  - `GET /api/v1/tools`
  - `GET /api/v1/tools/{toolName}/schema`
  - `POST /api/v1/tools/{toolName}/execute`
- Admin API：
  - `GET /api/v1/admin/catalog/status`
  - `POST /api/v1/admin/catalog/refresh`
- YAML 配置加载。
- app / tenant / tool 权限校验。
- 可插拔 schema registry，默认内存样例，可选 Nacos Config 后端。
- schema 查询和必填参数校验。
- traceId / requestId 透传。
- 统一响应 envelope 和错误码。
- 可插拔审计，默认日志输出，可选 JSONL 文件落地，不记录参数明文。
- Prometheus 文本格式 `/metrics` 指标出口，覆盖工具调用结果、耗时汇总和 Catalog 刷新快照。
- Prometheus 告警规则样例和观测接入说明。
- 可插拔限流，默认内存后端，可选 Redis token bucket 共享状态后端。
- 可插拔熔断，默认内存后端，可选 Redis 共享状态后端。
- 本地 Docker Redis 联调配置和治理共享状态 smoke 验证脚本。
- 可选主动健康检查。
- Discovery 失败保留最后一次 Catalog 快照。
- 可选定时 Catalog 刷新。
- MCP Server 注册 Nacos 的 Python helper、Java helper、生命周期封装、ephemeral 心跳能力和命令行示例。
- 本地 Docker Nacos 联调配置、示例 MCP Server 和 Nacos 专用 Gateway 配置。

### 2.2 文档产物

核心文档：

- 需求文档：`docs/codex/v1/requirements/mcp-gateway-nacos-discovery-requirements.md`
- 设计文档：`docs/codex/v1/designs/mcp-gateway-nacos-discovery-design.md`
- HTML 设计文档：`docs/codex/v1/designs/mcp-gateway-nacos-discovery-design.html`
- 补充方案：`docs/codex/v1/designs/MCP工具集成平台技术方案.md`
- 执行计划：`docs/codex/v1/plans/mcp-gateway-nacos-discovery-plan.md`
- Trace 审查：`docs/codex/v1/trace/mcp-gateway-nacos-discovery-trace.md`
- Nacos 联调说明：`docs/codex/v1/designs/mcp-gateway-nacos-integration-guide.md`
- 观测接入说明：`docs/codex/v1/operations/mcp-gateway-observability.md`
- MCP Server 注册模板：`docs/codex/v1/designs/mcp-server-nacos-registration-template.json`
- 本交付说明：`docs/codex/v1/delivery/mcp-gateway-mvp-delivery.md`

### 2.3 示例代码

- MCP Server 注册 helper、生命周期封装和 ephemeral 心跳能力：`src/mcp_gateway/examples/nacos_registration.py`
- 注册命令行示例：`examples/register_mcp_server_to_nacos.py`
- Java 注册 helper 示例：`examples/java/nacos-registration/`
- 本地示例 MCP Server：`examples/mock_mcp_server.py`
- 本地 Nacos compose：`docker-compose.nacos.yml`
- 本地 Redis compose：`docker-compose.redis.yml`
- Prometheus 告警规则样例：`deploy/prometheus/mcp-gateway-alerts.yml`
- Redis 治理 smoke 脚本：`examples/redis_governance_smoke.py`
- 本地 Nacos Gateway 配置：`config/mcp-gateway-nacos-local.yaml`
- Nacos Config schema 发布示例：`examples/publish_schemas_to_nacos.py`
- 本地 Redis Gateway 配置：`config/mcp-gateway-redis-local.yaml`
- Mock metadata：`src/mcp_gateway/examples/sample_metadata.py`
- Mock schemas：`src/mcp_gateway/examples/sample_schemas.py`

## 3. 运行方式

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

执行测试：

```powershell
python -m pytest
```

## 4. 配置说明

主配置文件：

```text
config/mcp-gateway.yaml
```

可通过环境变量指定配置文件：

```powershell
$env:MCP_GATEWAY_CONFIG="D:\path\to\mcp-gateway.yaml"
```

关键配置：

```yaml
discovery:
  mode: mock

mcp_client:
  mode: mock

nacos:
  enabled: false
  endpoint: http://127.0.0.1:8848
  namespace: dev
  group: MCP_SERVER_GROUP
  service_names:
    - mcp-server-knowledge
    - mcp-server-approval
    - mcp-server-document

health_check:
  enabled: false
  timeout_seconds: 1

catalog_refresh:
  enabled: false
  interval_seconds: 30
```

说明：

- 本地演示默认使用 `mock`。
- 接真实 Nacos 时，将 `discovery.mode` 改为 `nacos`，并设置 `nacos.enabled=true`。
- 本地 mock 模式下建议保持 `health_check.enabled=false`，避免探测不存在的本地 MCP Server 端口。
- 测试环境可开启 `catalog_refresh.enabled=true`，周期性刷新 Catalog。

## 5. MCP Server 注册示例

注册示例 MCP Server 到 Nacos：

```powershell
python examples/register_mcp_server_to_nacos.py `
  --endpoint http://127.0.0.1:8848 `
  --namespace dev `
  --group MCP_SERVER_GROUP `
  --service-name mcp-server-knowledge `
  --ip 127.0.0.1 `
  --port 18081
```

如果 Nacos 开启鉴权：

```powershell
python examples/register_mcp_server_to_nacos.py `
  --endpoint http://127.0.0.1:8848 `
  --namespace dev `
  --username nacos `
  --password nacos
```

注销示例：

```powershell
python examples/register_mcp_server_to_nacos.py `
  --endpoint http://127.0.0.1:8848 `
  --namespace dev `
  --service-name mcp-server-knowledge `
  --ip 127.0.0.1 `
  --port 18081 `
  --deregister
```

## 6. 验证结果

当前本地测试结果：

```text
81 passed
```

覆盖范围包括：

- API 工具列表、schema 查询、工具执行。
- Admin Catalog status / refresh。
- admin 权限保护。
- 权限配置加载。
- schema 必填参数校验，包括内存后端和 Nacos Config 后端。
- Nacos Config schema 发布 helper。
- metadata parser。
- Nacos discovery adapter。
- MCP Server 注册 helper、Java helper、生命周期封装和 ephemeral 心跳能力。
- Catalog / Router。
- audit 日志和 JSONL 文件审计落地。
- metrics 指标出口，包括工具调用计数、耗时汇总和 Catalog 刷新指标。
- Prometheus 告警规则样例。
- rate limiter，包括内存后端和 Redis 共享状态后端。
- circuit breaker，包括内存后端和 Redis 共享状态后端。
- health checker。
- Discovery 失败保留快照。
- 官方 Python MCP SDK Streamable HTTP Client adapter。
- 本地 Nacos 注册、发现、主动健康检查和 Streamable HTTP 调用联调。
- 本地 Redis 真实后端 smoke：限流桶和熔断打开状态可跨两个 Gateway 治理对象共享。

## 7. 对外交付口径

建议对外交付时使用以下口径：

> 当前版本为 MCP Gateway MVP / Nacos 联调样例版，已完成 MCP Server 注册元数据约定、Nacos 发现适配、Nacos Config schema 发布与读取、Tool Catalog、工具路由、三类 Tool mock 演示、权限、JSONL 审计落地、Prometheus `/metrics` 基础指标、告警规则样例、可插拔限流/熔断、健康检查、Python/Java 注册生命周期与 ephemeral 心跳示例和本地 Docker Nacos 联调。该版本可用于架构验证、本地演示和测试环境联调；生产上线前仍需完成公司测试/生产 Nacos 环境参数验证、真实业务系统接入、统一鉴权、审计中心/日志平台接入和公司指标平台采集配置。

## 8. 待完成事项

### 8.1 真实环境联调

| 待办 | 说明 | 优先级 |
| --- | --- | --- |
| 公司测试/生产 Nacos 环境参数验证 | 本地 Docker Nacos 已验证 discovery、schema config、健康检查和调用链路；仍需验证公司环境 endpoint、namespace、group、serviceName、鉴权和网络策略 | 高 |
| 真实 MCP Server 注册 | 已提供 Python/Java 注册生命周期 helper 和 ephemeral 心跳示例；真实业务 MCP Server 仍需在自身启动/关闭钩子中嵌入 | 高 |
| 真实业务 MCP Server 调用 | 本地示例 MCP Server 已验证 `tools/call`；仍需用真实业务 MCP Server endpoint 验证 | 高 |
| 生产心跳策略 | Python/Java helper 已支持 ephemeral 心跳示例；生产仍需按真实 MCP Server 框架和 Nacos 策略完成嵌入与压测 | 中 |

### 8.2 生产化治理

| 待办 | 说明 | 优先级 |
| --- | --- | --- |
| Redis 限流压测 | 已通过本地 Docker Redis smoke 验证共享限流桶，多副本上线前需做生产压测和评估降级策略 | 高 |
| Redis 熔断压测和指标 | 已通过本地 Docker Redis smoke 验证共享熔断状态，并具备 `/metrics` 基础出口和告警规则样例；多副本上线前需压测恢复窗口并校准阈值 | 高 |
| 统一鉴权 | 当前使用 `app_id` 和配置授权，需对接统一认证/权限中心 | 高 |
| 审计中心/日志平台接入 | 当前已支持日志输出和 JSONL 文件落地；生产仍需接 ES、日志平台或审计中心 | 中 |
| Metrics 指标平台接入 | 当前已提供 Prometheus 文本格式 `/metrics` 和告警规则样例，仍需接入公司指标平台并补齐采集配置 | 中 |

### 8.3 发现与路由增强

| 待办 | 说明 | 优先级 |
| --- | --- | --- |
| Nacos watch 推送 | 当前支持手动 refresh 和定时 refresh，尚未实现 watch 推送 | 中 |
| 灰度路由 | 设计中包含 labels/gray，当前未实现灰度策略 | 中 |
| 租户级路由 | 当前权限支持 tenant allow，Router 尚未支持 tenantMode 复杂筛选 | 中 |
| 权重调度增强 | 当前为简单轮询，可扩展加权轮询、最小延迟等策略 | 低 |

### 8.4 真实业务接入

| 待办 | 说明 | 优先级 |
| --- | --- | --- |
| 知识库真实 Tool | 当前 `knowledge.search` 为 mock，需要接真实知识库服务 | 高 |
| 审批真实 Tool | 当前 `approval.create_task` 为 mock，需要接真实审批系统 | 高 |
| 文档真实 Tool | 当前 `document.generate` 为 mock，需要接真实文档服务 | 高 |
| 业务 schema 确认 | 需要与业务方确认最终 input/output schema | 高 |

### 8.5 SDK 与协议演进

| 待办 | 说明 | 优先级 |
| --- | --- | --- |
| MCP 协议版本兼容 | metadata 已声明协议版本，后续需补多版本兼容策略 | 中 |
| schema 元数据服务演进 | 已支持 Nacos Config 后端；如后续需要版本审核、发布流和多环境回滚，可升级为独立元数据服务 | 中 |

## 9. 已知限制

- 当前默认使用 mock discovery、mock MCP client 和内存 schema registry；开启 `mcp_client.mode=streamable-http` 后使用官方 Python MCP SDK adapter，开启 `schema_registry.mode=nacos_config` 后从 Nacos Config 读取 schema。
- 当前三类 Tool 均为演示链路，不包含真实业务逻辑。
- 当前已通过本地 Docker Nacos 验证注册、发现、Nacos Config schema 读取和调用链路，尚未经过公司测试/生产 Nacos 环境验证。
- 当前限流、熔断已支持内存和 Redis 后端，并通过本地 Docker Redis smoke；生产多实例部署前仍需压测、容量评估和降级策略。
- 当前已提供基础 `/metrics` 指标出口、Prometheus 告警规则样例和 JSONL 文件审计落地，但尚未接入公司指标平台和审计中心。
- 当前没有 Nacos watch 推送，仅支持手动 refresh 和可选定时 refresh。

## 10. 建议下一步

建议下一步优先完成公司测试/生产 Nacos 环境参数验证：

1. 确认测试环境 Nacos `endpoint`、`namespace`、`group`、鉴权方式和网络策略。
2. 将注册 helper 嵌入真实 MCP Server 启动/关闭生命周期。
3. 如使用 Nacos ephemeral 实例，可复用 Python/Java helper 心跳能力，或使用服务自身 Nacos SDK。
4. Gateway 开启 `discovery.mode=nacos`、`nacos.enabled=true` 和 `mcp_client.mode=streamable-http`。
5. 调用 Admin refresh/status 验证 Catalog，并用真实 MCP Server 验证 `tools/call`。
6. 将测试环境差异回写到 `mcp-gateway-nacos-integration-guide.md`。
