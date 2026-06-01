# 生产观测能力推进

## 1. 恢复胶囊

- 任务需求：在已有 MCP Gateway MVP 基础上补齐生产级指标基础能力。
- 关键决策：先实现无新增依赖的 Prometheus 文本格式 `/metrics`，覆盖工具调用、结果码、耗时汇总和 Catalog 刷新快照；审计先落 JSONL 文件；告警先提供 Prometheus 样例规则，生产接入时再按压测结果校准阈值。
- 当前阶段：已完成基础指标、JSONL 审计、告警规则样例和文档同步。
- 已完成产物：`src/mcp_gateway/observability/metrics.py`、`/metrics` endpoint、工具调用与 Catalog 刷新埋点、JSONL 审计、`deploy/prometheus/mcp-gateway-alerts.yml`、`docs/codex/v1/operations/mcp-gateway-observability.md`、测试和文档更新。
- 剩余工作：接入公司指标平台、接入审计中心、生产压测并校准告警阈值。
- 重要发现：本地 Docker Nacos mock 数据联调已完成，不应再描述为“本地 Nacos 未联调”；剩余是公司测试/生产环境参数验证。

## 2. 步骤列表

- [v] 阅读现有 API、runtime、audit 边界。
- [v] 新增轻量 MetricsRegistry 和 Prometheus 文本渲染。
- [v] 在工具调用和 Catalog 刷新路径记录指标。
- [v] 暴露 `/metrics` endpoint。
- [v] 补充测试和文档状态。
- [~] 下一步：接入公司指标平台采集，或将 JSONL 审计文件接入公司审计中心。

## 3. 研究发现

- 工具调用指标适合在 `create_tools_router(...).execute_tool` 的 `finally` 与审计事件同源记录，能覆盖成功、权限失败、限流、下游失败等 result_code。
- Catalog 刷新指标适合在 `GatewayRuntime.refresh_catalog()` 成功或使用快照降级后记录，首次 discovery 失败仍抛出异常，不生成快照指标。
- 当前实现不引入 prometheus-client 依赖，避免扩大依赖面；后续如公司平台要求标准 Histogram/Summary，可替换或适配。

## 4. 验证记录

- `python -m pytest tests/test_metrics.py tests/test_api.py tests/test_runtime_snapshot.py`：18 passed。
- `python -m pytest`：69 passed。

## 5. 审计落地推进

- [v] 新增 `audit` 配置模型，默认 `logging`，可选 `file`。
- [v] 新增 `JsonlFileAuditLogger`，按 JSON Lines 写入审计事件。
- [v] 主应用改为通过 `create_audit_logger(config)` 创建审计后端。
- [v] 补充配置、API 链路和文件审计测试。
- [~] 下一步：将 JSONL 审计文件接入公司日志平台/审计中心，或继续补告警规则样例。

## 6. 审计验证记录

- `python -m pytest tests/test_audit.py tests/test_config_policy.py tests/test_api.py`：26 passed。
- `python -m pytest`：74 passed。
- `python -m pytest tests/test_observability_docs.py`：1 passed。
- `python -m pytest`：75 passed。

## 7. 告警规则样例推进

- [v] 新增 Prometheus 告警规则样例 `deploy/prometheus/mcp-gateway-alerts.yml`。
- [v] 新增观测接入说明 `docs/codex/v1/operations/mcp-gateway-observability.md`。
- [v] 补充规则文件结构测试，确认核心告警和指标引用存在。
- [~] 下一步：接入公司 Prometheus/指标平台并按压测结果校准阈值。
