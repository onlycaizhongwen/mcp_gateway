# MCP Gateway MVP

本项目是 MCP Gateway 的 Python/FastAPI MVP 实现，用于验证企业 AI 升级项目中 MCP 工具层的核心链路：MCP Server 注册到 Nacos，MCP Gateway 动态发现、聚合工具目录并统一调度调用。

当前版本定位为 **MCP Gateway MVP / Nacos 联调样例版**，适合架构验证、本地演示、测试环境联调和 MCP Tool 接入规范参考，不建议直接作为生产版本发布。

## 已包含能力

- Mock Nacos discovery，内置示例 MCP Server metadata。
- 可选 Nacos OpenAPI discovery adapter。
- Tool Catalog 聚合，支持 `knowledge.search`、`approval.create_task`、`document.generate`。
- 基础 Router/Scheduler，按健康实例选择目标 MCP Server。
- HTTP API：
  - `GET /api/v1/tools`
  - `GET /api/v1/tools/{toolName}/schema`
  - `POST /api/v1/tools/{toolName}/execute`
- Mock MCP client，支持知识库搜索、审批任务创建、文档生成三类演示工具。
- 可选官方 Python MCP SDK Streamable HTTP client adapter。
- 基于 `app_id` 的基础权限校验。
- 从 `config/mcp-gateway.yaml` 加载 YAML 权限配置。
- 可插拔 schema registry，默认内存样例，可选 Nacos Config 后端。
- traceId / requestId 统一响应封装。
- 可插拔审计，默认日志输出，可选 JSONL 文件落地；记录调用路由、耗时和结果码，不记录参数明文。
- Prometheus 文本格式 `/metrics` 指标出口，记录工具调用结果、耗时汇总和 Catalog 刷新快照。
- Admin API，支持 Catalog 状态查询和手动刷新。
- 可插拔熔断，默认内存后端，可选 Redis 共享状态后端。
- 可插拔限流，按 app、tenant、tool 维度控制调用，默认内存后端，可选 Redis token bucket。
- 可选主动健康检查。
- Nacos discovery 失败后保留最后一次成功 Catalog 快照。
- 可选定时 Catalog 刷新，无需手动调用 admin refresh。
- MCP Server 注册到 Nacos 的 helper 和命令行示例。

## 本地运行

安装依赖：

```powershell
python -m pip install -e ".[dev]"
```

启动服务：

```powershell
python -m uvicorn mcp_gateway.main:app --reload
```

使用自定义配置文件：

```powershell
$env:MCP_GATEWAY_CONFIG="D:\path\to\mcp-gateway.yaml"
python -m uvicorn mcp_gateway.main:app --reload
```

打开 API 文档：

```text
http://127.0.0.1:8000/docs
```

## Nacos 发现配置

如需启用真实 Nacos discovery，可修改 `config/mcp-gateway.yaml`：

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

Nacos 联调说明和 MCP Server 注册 metadata 模板：

- `docs/codex/v1/designs/mcp-gateway-nacos-integration-guide.md`
- `docs/codex/v1/designs/mcp-server-nacos-registration-template.json`

MCP Server 注册示例：

- `src/mcp_gateway/examples/nacos_registration.py`
- `examples/register_mcp_server_to_nacos.py`

注册示例 MCP Server：

```powershell
python examples/register_mcp_server_to_nacos.py `
  --endpoint http://127.0.0.1:8848 `
  --namespace dev `
  --service-name mcp-server-knowledge `
  --ip 127.0.0.1 `
  --port 18081
```

## MCP Client 配置

调用真实 MCP Server 时，可开启官方 Python MCP SDK Streamable HTTP adapter：

```yaml
mcp_client:
  mode: streamable-http
  timeout_seconds: 10
```

## 治理配置

治理状态后端默认使用进程内内存，适合本地演示和单实例运行：

```yaml
state_backend:
  mode: memory
```

多 Gateway 副本部署时，可切换到 Redis 共享状态后端：

```yaml
state_backend:
  mode: redis
  redis:
    url: redis://127.0.0.1:6379/0
    key_prefix: mcp-gateway
    socket_timeout_seconds: 1
```

本地 Redis 联调：

```powershell
docker compose -f docker-compose.redis.yml up -d
python examples/redis_governance_smoke.py
```

当前本地验证结果：真实 Redis 中限流桶和熔断打开状态均可跨两个 Gateway 治理对象共享。

熔断配置：

```yaml
circuit_breaker:
  enabled: true
  failure_threshold: 3
  recovery_seconds: 30
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

主动健康检查默认关闭，避免本地 mock 模式误探真实端口：

```yaml
health_check:
  enabled: false
  timeout_seconds: 1
```

定时 Catalog 刷新默认关闭：

```yaml
catalog_refresh:
  enabled: false
  interval_seconds: 30
```

Schema registry 默认使用内存样例，适合本地演示：

```yaml
schema_registry:
  mode: memory
```

测试环境可切换到 Nacos Config。`nacos://mcp-schemas/knowledge.search/1.0.0/input` 会映射为 `dataId=mcp-schemas__knowledge.search__1.0.0__input.json`：

```yaml
schema_registry:
  mode: nacos_config
  nacos_config:
    group: MCP_SCHEMA_GROUP
```

审计默认写日志。需要文件落地时，可切换为 JSONL：

```yaml
audit:
  mode: file
  file:
    path: logs/mcp-gateway-audit.jsonl
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

Catalog 管理接口：

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri http://127.0.0.1:8000/api/v1/admin/catalog/status `
  -Headers @{"x-app-id"="internal-ai-agent"}

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/admin/catalog/refresh `
  -Headers @{"x-app-id"="internal-ai-agent"}
```

查看 Prometheus 指标：

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/metrics
```

调用知识库搜索：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/tools/knowledge.search/execute `
  -ContentType "application/json" `
  -Body '{"tenant_id":"tenant-a","app_id":"internal-ai-agent","arguments":{"query":"年假政策","top_k":1}}'
```

创建审批任务：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/tools/approval.create_task/execute `
  -ContentType "application/json" `
  -Body '{"tenant_id":"tenant-a","app_id":"internal-ai-agent","arguments":{"title":"合同审批","applicant":"u001","approver":"u002","payload":{"amount":1000}}}'
```

生成文档：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/tools/document.generate/execute `
  -ContentType "application/json" `
  -Body '{"tenant_id":"tenant-a","app_id":"internal-ai-agent","arguments":{"template":"contract.summary","title":"合同摘要","variables":{"customer":"示例客户"}}}'
```

## 测试

```powershell
python -m pytest
```

当前验证结果：`74 passed`。

## 交付说明

完整交付说明见：

```text
docs/codex/v1/delivery/mcp-gateway-mvp-delivery.md
```

该文档包含交付范围、运行方式、验证结果、对外交付口径、已知限制和待完成事项。

## 待完成事项

- 完成真实 Nacos 测试环境联调。
- 对 Redis 限流、熔断共享状态做生产压测，并基于 `/metrics` 接入生产指标告警。
- 接入真实知识库、审批、文档业务系统。
- 接入公司审计中心/日志平台、告警规则和指标平台采集配置。
