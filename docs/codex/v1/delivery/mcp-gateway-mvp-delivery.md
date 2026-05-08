# MCP Gateway MVP 交付说明

版本：v1  
主题：mcp-gateway-nacos-discovery  
交付日期：2026-05-06

## 1. 交付定位

本次交付为 **MCP Gateway MVP / Nacos 联调样例版**。

该版本用于验证明源云 AI 升级项目中 MCP 工具层的核心链路：MCP Server 通过 Nacos 注册工具元数据，MCP Gateway 发现、聚合、调度并对上游提供统一工具查询和调用入口。

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
- Streamable HTTP JSON-RPC MCP Client adapter 骨架。
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
- schema 查询和必填参数校验。
- traceId / requestId 透传。
- 统一响应 envelope 和错误码。
- 最小审计日志。
- 基础内存限流。
- 最小内存熔断。
- 可选主动健康检查。
- Discovery 失败保留最后一次 Catalog 快照。
- 可选定时 Catalog 刷新。
- MCP Server 注册 Nacos 的 Python helper 和命令行示例。

### 2.2 文档产物

核心文档：

- 需求文档：`docs/codex/v1/requirements/mcp-gateway-nacos-discovery-requirements.md`
- 设计文档：`docs/codex/v1/designs/mcp-gateway-nacos-discovery-design.md`
- HTML 设计文档：`docs/codex/v1/designs/mcp-gateway-nacos-discovery-design.html`
- 补充方案：`docs/codex/v1/designs/MCP工具集成平台技术方案.md`
- 执行计划：`docs/codex/v1/plans/mcp-gateway-nacos-discovery-plan.md`
- Trace 审查：`docs/codex/v1/trace/mcp-gateway-nacos-discovery-trace.md`
- Nacos 联调说明：`docs/codex/v1/designs/mcp-gateway-nacos-integration-guide.md`
- MCP Server 注册模板：`docs/codex/v1/designs/mcp-server-nacos-registration-template.json`
- 本交付说明：`docs/codex/v1/delivery/mcp-gateway-mvp-delivery.md`

### 2.3 示例代码

- MCP Server 注册 helper：`src/mcp_gateway/examples/nacos_registration.py`
- 注册命令行示例：`examples/register_mcp_server_to_nacos.py`
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
52 passed
```

覆盖范围包括：

- API 工具列表、schema 查询、工具执行。
- Admin Catalog status / refresh。
- admin 权限保护。
- 权限配置加载。
- schema 必填参数校验。
- metadata parser。
- Nacos discovery adapter。
- MCP Server 注册 helper。
- Catalog / Router。
- audit 日志。
- rate limiter。
- circuit breaker。
- health checker。
- Discovery 失败保留快照。
- Streamable HTTP MCP Client adapter。

## 7. 对外交付口径

建议对外交付时使用以下口径：

> 当前版本为 MCP Gateway MVP / Nacos 联调样例版，已完成 MCP Server 注册元数据约定、Nacos 发现适配、Tool Catalog、工具路由、三类 Tool mock 演示、权限、审计、限流、熔断、健康检查和注册示例。该版本可用于架构验证、本地演示和测试环境联调；生产上线前仍需完成真实 Nacos/MCP Server 联调、真实业务系统接入、统一鉴权和分布式治理能力增强。

## 8. 待完成事项

### 8.1 真实环境联调

| 待办 | 说明 | 优先级 |
| --- | --- | --- |
| 真实 Nacos 联调 | 验证 endpoint、namespace、group、serviceName、鉴权和 metadata 嵌套格式 | 高 |
| 真实 MCP Server 注册 | 将注册 helper 嵌入 MCP Server 启动/关闭生命周期 | 高 |
| 真实 Streamable HTTP 调用 | 用真实 MCP Server endpoint 验证 `tools/call` | 高 |
| 健康检查联调 | 验证 MCP Server `/health` 与 Gateway 主动探活策略 | 中 |

### 8.2 生产化治理

| 待办 | 说明 | 优先级 |
| --- | --- | --- |
| 分布式限流 | 当前限流为进程内 token bucket，多副本需改 Redis、网关或服务网格方案 | 高 |
| 分布式熔断/指标 | 当前熔断为进程内状态，需接入指标系统或共享状态 | 高 |
| 统一鉴权 | 当前使用 `app_id` 和配置授权，需对接统一认证/权限中心 | 高 |
| 审计落库或日志平台 | 当前为日志记录，应接 ES、日志平台或审计中心 | 中 |
| Metrics 指标 | 补 Prometheus 或内部指标平台埋点 | 中 |

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
| 官方 MCP SDK adapter | 当前 Streamable HTTP client 是最小 JSON-RPC adapter | 中 |
| MCP 协议版本兼容 | metadata 已声明协议版本，后续需补多版本兼容策略 | 中 |
| schema 存储迁移 | 当前 schema 在内存样例中，后续可迁移到 Nacos Config 或元数据服务 | 中 |

## 9. 已知限制

- 当前默认使用 mock discovery 和 mock MCP client。
- 当前三类 Tool 均为演示链路，不包含真实业务逻辑。
- 当前 Nacos adapter 未经过真实 Nacos 测试环境验证。
- 当前限流、熔断为进程内实现，不适合多实例生产部署。
- 当前没有完整指标系统和审计持久化。
- 当前没有 Nacos watch 推送，仅支持手动 refresh 和可选定时 refresh。

## 10. 建议下一步

建议下一步优先完成真实 Nacos 测试环境联调：

1. 确认 Nacos `endpoint`、`namespace`、`group`、鉴权方式。
2. 使用注册示例注册 `mcp-server-knowledge`。
3. Gateway 开启 `discovery.mode=nacos` 和 `nacos.enabled=true`。
4. 调用 Admin refresh/status 验证 Catalog。
5. 开启 `mcp_client.mode=streamable-http`，验证真实 MCP `tools/call`。
6. 将联调差异回写到 `mcp-gateway-nacos-integration-guide.md`。
