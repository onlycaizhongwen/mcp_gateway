# MCP Gateway Nacos 联调说明

## 1. Nacos 配置

Gateway 侧配置示例：

```yaml
discovery:
  mode: nacos
nacos:
  enabled: true
  endpoint: http://nacos.example.com:8848
  namespace:
  group: MCP_SERVER_GROUP
  service_names:
    - mcp-server-knowledge
  username:
  password:
  timeout_seconds: 3
health_check:
  enabled: true
  timeout_seconds: 1
schema_registry:
  mode: nacos_config
  nacos_config:
    group: MCP_SCHEMA_GROUP
```

## 2. MCP Server 注册约定

MCP Server 注册到 Nacos 时，需要在实例 metadata 中携带 MCP 工具元数据。模板见：

`docs/codex/v1/designs/mcp-server-nacos-registration-template.json`

仓库内也提供了一个 Python 注册示例：

- helper：`src/mcp_gateway/examples/nacos_registration.py`
- 命令行示例：`examples/register_mcp_server_to_nacos.py`

Python MCP Server 可使用 `McpServerNacosLifecycle` 在启动时注册、关闭时注销：

```python
from mcp_gateway.examples.nacos_registration import (
    McpServerNacosLifecycle,
    McpServerRegistration,
    NacosMcpServerRegistrar,
    NacosRegistrationConfig,
    knowledge_search_metadata,
)

registrar = NacosMcpServerRegistrar(
    NacosRegistrationConfig(
        endpoint="http://127.0.0.1:8848",
        group="MCP_SERVER_GROUP",
    )
)
lifecycle = McpServerNacosLifecycle(
    registrar,
    McpServerRegistration(
        service_name="mcp-server-knowledge",
        ip="127.0.0.1",
        port=18081,
        metadata=knowledge_search_metadata(),
    ),
)

lifecycle.start()
# 在 MCP Server shutdown hook 中调用：
lifecycle.stop()
```

如注册为 Nacos ephemeral 临时实例，可开启心跳线程：

```python
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
```

真实 Nacos 对实例 `metadata` 更适合使用字符串 map。当前注册 helper 会把 MCP 元数据写入 `metadata.mcp` JSON 字符串，Gateway discovery 会自动解析该字段。

本地或测试环境可这样注册一个示例 MCP Server 到 public namespace：

```powershell
python examples/register_mcp_server_to_nacos.py `
  --endpoint http://127.0.0.1:8848 `
  --group MCP_SERVER_GROUP `
  --service-name mcp-server-knowledge `
  --ip 127.0.0.1 `
  --port 18081
```

如果 Nacos 开启鉴权：

```powershell
python examples/register_mcp_server_to_nacos.py `
  --endpoint http://127.0.0.1:8848 `
  --username nacos `
  --password nacos
```

注销示例实例：

```powershell
python examples/register_mcp_server_to_nacos.py `
  --endpoint http://127.0.0.1:8848 `
  --service-name mcp-server-knowledge `
  --ip 127.0.0.1 `
  --port 18081 `
  --deregister
```

关键字段：

- `metadataVersion`：当前使用 `1.0`。
- `mcpProtocolVersion`：当前按设计使用 `2025-03-26`。
- `transport`：MVP 使用 `streamable-http`。
- `endpoint`：Gateway 调用 `tools/call` 的 MCP endpoint。
- `healthPath`：Gateway 主动健康检查路径。
- `tools[].name`：工具名，例如 `knowledge.search`。
- `tools[].inputSchemaRef` / `outputSchemaRef`：schema 引用地址。

## 3. Schema 配置发布约定

工具 schema 不放在 Nacos instance metadata 中，而是通过 `schemaRef` 指向 Nacos Config。

当前本地约定：

- `group`：`MCP_SCHEMA_GROUP`
- `nacos://mcp-schemas/knowledge.search/1.0.0/input` 映射为 `dataId=mcp-schemas__knowledge.search__1.0.0__input.json`
- `nacos://mcp-schemas/knowledge.search/1.0.0/output` 映射为 `dataId=mcp-schemas__knowledge.search__1.0.0__output.json`

发布仓库内 mock schema 到本地 Nacos Config：

```powershell
python examples/publish_schemas_to_nacos.py `
  --endpoint http://127.0.0.1:8848 `
  --group MCP_SCHEMA_GROUP
```

## 4. Gateway 发现行为

- Nacos 返回的实例会先做 metadata 解析，非法实例会被跳过。
- 开启 `health_check.enabled` 后，Gateway 会访问实例 `healthPath`。
- 开启主动健康检查时，Gateway 以实际 `/health` 探活结果作为路由健康状态；这适合本地一次性注册示例，也便于覆盖 Nacos 未维护心跳导致的临时健康状态。
- 探活失败实例不会进入 Router 的 provider 候选集。
- 如果 Nacos 短暂不可用，且 Gateway 已有上一次成功 Catalog，刷新会保留旧快照并返回 `used_snapshot=true`。
- 如果首次启动就无法连接 Nacos，Gateway 会暴露启动失败，避免空目录静默运行。

## 5. 联调验证

1. 启动或复用本地 Nacos：

```powershell
docker compose -f docker-compose.nacos.yml up -d
```

2. 启动示例 MCP Server：

```powershell
python -m uvicorn examples.mock_mcp_server:app --host 127.0.0.1 --port 18081
```

该示例服务使用官方 Python MCP SDK 的 FastMCP，能够完整响应 Streamable HTTP 的 `initialize`、`initialized` 和 `tools/call` 协议流。

3. MCP Server 注册到 Nacos：

```powershell
python examples/register_mcp_server_to_nacos.py `
  --endpoint http://127.0.0.1:8848 `
  --group MCP_SERVER_GROUP `
  --service-name mcp-server-knowledge `
  --ip 127.0.0.1 `
  --port 18081
```

4. 发布 mock schema 到 Nacos Config：

```powershell
python examples/publish_schemas_to_nacos.py `
  --endpoint http://127.0.0.1:8848 `
  --group MCP_SCHEMA_GROUP
```

5. 启动 Gateway，并配置 `discovery.mode=nacos`、`mcp_client.mode=streamable-http`、`schema_registry.mode=nacos_config`：

```powershell
$env:MCP_GATEWAY_CONFIG="D:\czw_ai_project\mcp_gateway\config\mcp-gateway-nacos-local.yaml"
python -m uvicorn mcp_gateway.main:app --host 127.0.0.1 --port 18080
```

6. 调用 Admin refresh：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:18080/api/v1/admin/catalog/refresh `
  -Headers @{"x-app-id"="internal-ai-agent"}
```

7. 查看 Catalog 状态：

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri http://127.0.0.1:18080/api/v1/admin/catalog/status `
  -Headers @{"x-app-id"="internal-ai-agent"}
```

8. 查询工具 schema，验证 Gateway 从 Nacos Config 读取 schema：

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri http://127.0.0.1:18080/api/v1/tools/knowledge.search/schema
```

9. 调用工具：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:18080/api/v1/tools/knowledge.search/execute `
  -ContentType "application/json" `
  -Body '{"tenant_id":"tenant-a","app_id":"internal-ai-agent","arguments":{"query":"local nacos integration","top_k":1}}'
```

本地验证结果：

- `/health` 返回 `instance_count=1`、`healthy_instance_count=1`。
- Catalog 状态返回 `tools=1`、`instances=1`、`healthyInstances=1`。
- `/api/v1/tools/knowledge.search/schema` 返回 Nacos Config 中发布的 input/output schema。
- 缺少 `query` 参数时返回 `MCP_TOOL_VALIDATION_FAILED`，证明 schema 校验走 Nacos Config 后端。
- 工具调用通过官方 Python MCP SDK Streamable HTTP adapter 返回示例 FastMCP Server 结果。
