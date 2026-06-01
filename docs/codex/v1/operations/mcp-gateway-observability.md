# MCP Gateway 观测接入说明

## 1. 目标

本文档说明 MCP Gateway 当前可交付的观测能力，以及测试/生产环境接入 Prometheus、日志平台和审计中心时的建议配置。

当前已具备：

- `/metrics` Prometheus 文本格式指标出口。
- JSONL 文件审计落地。
- traceId / requestId 透传。
- 工具调用 result_code。
- Catalog refresh 快照指标。

当前仍需生产接入方完成：

- 指标平台采集配置。
- 告警通知路由。
- JSONL 审计文件采集到日志平台或审计中心。
- 生产压测后的阈值校准。

## 2. Metrics 采集

Gateway 暴露指标地址：

```text
GET /metrics
```

Prometheus scrape 示例：

```yaml
scrape_configs:
  - job_name: mcp-gateway
    metrics_path: /metrics
    static_configs:
      - targets:
          - mcp-gateway.example.com:8000
```

本地验证：

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8000/metrics
```

## 3. 核心指标

| 指标 | 类型 | 含义 | 主要用途 |
| --- | --- | --- | --- |
| `mcp_gateway_tool_calls_total` | counter | 工具调用总数，带 `tool_name` 和 `result_code` 标签 | QPS、错误率、限流、下游不可用 |
| `mcp_gateway_tool_call_duration_ms_count` | counter | 工具调用耗时样本数 | 平均耗时计算 |
| `mcp_gateway_tool_call_duration_ms_sum` | counter | 工具调用耗时总和，单位 ms | 平均耗时计算 |
| `mcp_gateway_catalog_refresh_total` | counter | Catalog 刷新次数，带 `result=success|failure|snapshot` 标签 | Discovery/Nacos 可用性 |
| `mcp_gateway_catalog_tools` | gauge | 当前 Catalog 工具数 | 目录完整性 |
| `mcp_gateway_catalog_instances` | gauge | 当前实例总数 | 注册发现状态 |
| `mcp_gateway_catalog_healthy_instances` | gauge | 当前健康实例数 | 可用性 |
| `mcp_gateway_catalog_unavailable_instances` | gauge | 当前不可用实例数 | 故障定位 |

## 4. 告警规则

样例规则文件：

```text
deploy/prometheus/mcp-gateway-alerts.yml
```

当前样例覆盖：

- 工具调用错误率过高。
- 限流过高。
- MCP Server 无可用实例。
- Catalog refresh 失败或使用快照降级。
- 健康实例数为 0。
- 平均调用耗时过高。

注意：当前耗时指标只有 sum/count，样例只能计算平均耗时。生产若需要 P95/P99，应将网关指标升级为 histogram。

## 5. 审计采集

默认配置为日志输出：

```yaml
audit:
  mode: logging
```

文件落地配置：

```yaml
audit:
  mode: file
  file:
    path: logs/mcp-gateway-audit.jsonl
```

JSONL 每行一条工具调用审计事件，字段包括：

| 字段 | 含义 |
| --- | --- |
| `created_at` | 审计生成时间 |
| `trace_id` | 链路追踪 ID |
| `request_id` | 请求 ID |
| `app_id` | 调用应用 |
| `tenant_id` | 租户 |
| `tool_name` | 工具名 |
| `result_code` | 结果码 |
| `duration_ms` | 调用耗时 |
| `route_instance_id` | 路由到的 MCP Server 实例 |
| `route_service_name` | 路由到的服务名 |
| `argument_keys` | 参数 key 列表 |

审计不记录参数明文。日志平台采集时建议按 `trace_id`、`request_id`、`app_id`、`tenant_id`、`tool_name`、`result_code` 建索引。

## 6. Dashboard 建议

建议至少建立以下面板：

- 总调用量：`sum(rate(mcp_gateway_tool_calls_total[5m]))`
- 错误率：`sum(rate(mcp_gateway_tool_calls_total{result_code!="0"}[5m])) / clamp_min(sum(rate(mcp_gateway_tool_calls_total[5m])), 1)`
- 限流量：`sum(rate(mcp_gateway_tool_calls_total{result_code="MCP_RATE_LIMITED"}[5m]))`
- 下游不可用：`sum(rate(mcp_gateway_tool_calls_total{result_code="MCP_SERVER_UNAVAILABLE"}[5m]))`
- 平均耗时：`sum(rate(mcp_gateway_tool_call_duration_ms_sum[5m])) / clamp_min(sum(rate(mcp_gateway_tool_call_duration_ms_count[5m])), 1)`
- 健康实例数：`mcp_gateway_catalog_healthy_instances`
- Catalog 刷新降级：`sum(rate(mcp_gateway_catalog_refresh_total{result=~"failure|snapshot"}[5m]))`

## 7. 生产接入检查项

- 确认 `/metrics` 只暴露在内网或受网关访问控制保护。
- 确认 Prometheus scrape 周期，建议 15s 到 60s。
- 根据压测结果调整告警阈值。
- 确认 JSONL 文件轮转和磁盘保留策略。
- 确认审计日志采集链路不会采集参数明文。
- 确认告警路由到对应值班组。
- 将公司测试/生产 Nacos 的 endpoint、namespace、group 和 serviceName 纳入 dashboard 标签或环境标签。
