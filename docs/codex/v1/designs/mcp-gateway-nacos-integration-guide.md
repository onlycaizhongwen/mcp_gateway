# MCP Gateway Nacos 联调说明

## 1. Nacos 配置

Gateway 侧配置示例：

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
  username:
  password:
  timeout_seconds: 3
health_check:
  enabled: true
  timeout_seconds: 1
```

## 2. MCP Server 注册约定

MCP Server 注册到 Nacos 时，需要在实例 metadata 中携带 MCP 工具元数据。模板见：

`docs/codex/v1/designs/mcp-server-nacos-registration-template.json`

仓库内也提供了一个 Python 注册示例：

- helper：`src/mcp_gateway/examples/nacos_registration.py`
- 命令行示例：`examples/register_mcp_server_to_nacos.py`

本地或测试环境可这样注册一个示例 MCP Server：

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

注销示例实例：

```powershell
python examples/register_mcp_server_to_nacos.py `
  --endpoint http://127.0.0.1:8848 `
  --namespace dev `
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

## 3. Gateway 发现行为

- Nacos 返回的实例会先做 metadata 解析，非法实例会被跳过。
- 开启 `health_check.enabled` 后，Gateway 会访问实例 `healthPath`。
- 探活失败实例不会进入 Router 的 provider 候选集。
- 如果 Nacos 短暂不可用，且 Gateway 已有上一次成功 Catalog，刷新会保留旧快照并返回 `used_snapshot=true`。
- 如果首次启动就无法连接 Nacos，Gateway 会暴露启动失败，避免空目录静默运行。

## 4. 联调验证

1. MCP Server 注册到 Nacos。
2. 启动 Gateway 并配置 `discovery.mode=nacos`。
3. 调用 Admin refresh：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/admin/catalog/refresh `
  -Headers @{"x-app-id"="internal-ai-agent"}
```

4. 查看 Catalog 状态：

```powershell
Invoke-RestMethod `
  -Method Get `
  -Uri http://127.0.0.1:8000/api/v1/admin/catalog/status `
  -Headers @{"x-app-id"="internal-ai-agent"}
```

5. 调用工具：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/tools/knowledge.search/execute `
  -ContentType "application/json" `
  -Body '{"tenant_id":"tenant-a","app_id":"internal-ai-agent","arguments":{"query":"年假政策","top_k":1}}'
```
