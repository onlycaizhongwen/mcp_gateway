# MCP Gateway MVP

Python/FastAPI implementation of the MCP Gateway MVP described in `docs/codex/v1`.

## What is included

- Mock Nacos discovery with sample MCP Server metadata.
- Optional Nacos OpenAPI discovery adapter.
- Tool Catalog aggregation for `knowledge.search`, `approval.create_task`, and `document.generate`.
- Basic router/scheduler with healthy instance selection.
- HTTP API adapter:
  - `GET /api/v1/tools`
  - `POST /api/v1/tools/{toolName}/execute`
- Mock MCP client for knowledge search, approval task creation, and document generation.
- Optional Streamable HTTP MCP client adapter.
- Basic policy check by `app_id`.
- YAML permission config loaded from `config/mcp-gateway.yaml`.
- Tool schema lookup through an in-memory schema registry.
- Trace/request id envelope.
- Minimal audit logging for tool calls, including route and duration without argument values.
- Admin APIs for Catalog status and manual refresh.
- Minimal in-memory circuit breaker for downstream MCP Server failures.
- Basic in-memory rate limiting by app, tenant, and tool.
- Optional active MCP Server health checks during Catalog refresh.
- Catalog snapshot preservation when Nacos discovery refresh fails after a previous success.
- Optional periodic Catalog refresh for dynamic discovery without manual admin calls.

## Run locally

```powershell
python -m pip install -e ".[dev]"
python -m uvicorn mcp_gateway.main:app --reload
```

To use a different config file:

```powershell
$env:MCP_GATEWAY_CONFIG="D:\path\to\mcp-gateway.yaml"
python -m uvicorn mcp_gateway.main:app --reload
```

To enable Nacos discovery, update `config/mcp-gateway.yaml`:

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

Nacos integration notes and an MCP Server registration metadata template are available at:

- `docs/codex/v1/designs/mcp-gateway-nacos-integration-guide.md`
- `docs/codex/v1/designs/mcp-server-nacos-registration-template.json`

An example MCP Server registration helper is available at:

- `src/mcp_gateway/examples/nacos_registration.py`
- `examples/register_mcp_server_to_nacos.py`

Example:

```powershell
python examples/register_mcp_server_to_nacos.py `
  --endpoint http://127.0.0.1:8848 `
  --namespace dev `
  --service-name mcp-server-knowledge `
  --ip 127.0.0.1 `
  --port 18081
```

To call real MCP Server endpoints through Streamable HTTP:

```yaml
mcp_client:
  mode: streamable-http
  timeout_seconds: 10
```

Circuit breaker defaults:

```yaml
circuit_breaker:
  enabled: true
  failure_threshold: 3
  recovery_seconds: 30
```

Rate limits are configured per app:

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

Active health checks are disabled by default for local mock mode:

```yaml
health_check:
  enabled: false
  timeout_seconds: 1
```

Periodic Catalog refresh is also disabled by default:

```yaml
catalog_refresh:
  enabled: false
  interval_seconds: 30
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Example calls

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/v1/tools
```

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/api/v1/tools/knowledge.search/schema
```

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

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/tools/knowledge.search/execute `
  -ContentType "application/json" `
  -Body '{"tenant_id":"tenant-a","app_id":"internal-ai-agent","arguments":{"query":"年假政策","top_k":1}}'
```

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/tools/approval.create_task/execute `
  -ContentType "application/json" `
  -Body '{"tenant_id":"tenant-a","app_id":"internal-ai-agent","arguments":{"title":"合同审批","applicant":"u001","approver":"u002","payload":{"amount":1000}}}'
```

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/tools/document.generate/execute `
  -ContentType "application/json" `
  -Body '{"tenant_id":"tenant-a","app_id":"internal-ai-agent","arguments":{"template":"contract.summary","title":"合同摘要","variables":{"customer":"明源云"}}}'
```

## Test

```powershell
python -m pytest
```

## Next steps

- Replace the minimal Streamable HTTP client with the official Python MCP SDK adapter when the SDK version is locked.
- Replace in-memory schema registry with Nacos Config or metadata service.
- Add production-grade circuit breaker metrics, distributed rate limiting, and real business system adapters.
