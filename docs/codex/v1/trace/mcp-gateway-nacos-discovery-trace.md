# MCP 网关 Nacos 服务发现 Trace 审查

版本：v1  
主题：mcp-gateway-nacos-discovery  
审查日期：2026-05-06

## 1. 审查范围

本次审查对照以下材料：

- 需求：`docs/codex/v1/requirements/mcp-gateway-nacos-discovery-requirements.md`
- 设计：`docs/codex/v1/designs/mcp-gateway-nacos-discovery-design.md`
- 补充方案：`docs/codex/v1/designs/MCP工具集成平台技术方案.md`
- 计划：`docs/codex/v1/plans/mcp-gateway-nacos-discovery-plan.md`
- 实现：`src/mcp_gateway/**`、`config/mcp-gateway.yaml`
- 测试：`tests/**`

## 2. 总体结论

当前主题已完成 MCP Gateway MVP 的主要闭环：本地 mock discovery、Nacos discovery adapter、Tool Catalog、Router、HTTP API、三类演示 Tool、schema 校验、可插拔 schema registry、权限、审计文件落地、基础 metrics 指标、Prometheus 告警规则样例、限流、熔断、主动健康检查、Catalog 管理接口、本地 Docker Nacos 联调材料和发现失败快照保留策略均已落地。

验证结果：`python -m pytest` 通过，当前测试集 `79 passed`；本地 Docker Nacos 联调中，Gateway 发现 `knowledge.search`，`providers=1`，通过 Nacos Config 读取 mock schema，缺参校验返回 `MCP_TOOL_VALIDATION_FAILED`，并通过 Streamable HTTP `tools/call` 调用示例 MCP Server 成功。当前 Streamable HTTP client 已替换为官方 Python MCP SDK adapter，并完成本地 FastMCP 示例服务端到端烟测。

结论：MVP 实现与当前 plan 的阶段 1 到阶段 11 基本一致，可以作为本地演示和公司测试环境 Nacos 参数验证前置版本。生产级接入仍需要公司测试/生产 Nacos 环境参数验证、真实业务 MCP Server、统一鉴权、生产压测、指标平台采集配置和告警阈值校准等后续工作。

## 3. 已对齐项

| 需求/设计承诺 | 实现情况 | 证据 |
| --- | --- | --- |
| MCP Server 注册模型与 Nacos metadata 约定 | 已提供 sample metadata、Nacos 注册模板和 metadata parser | `src/mcp_gateway/examples/sample_metadata.py`、`docs/codex/v1/designs/mcp-server-nacos-registration-template.json`、`src/mcp_gateway/discovery/metadata_parser.py` |
| MCP Server 注册示例 | 已提供 Python 注册 helper 和命令行示例，并按真实 Nacos 兼容格式写入 `metadata.mcp` JSON 字符串 | `src/mcp_gateway/examples/nacos_registration.py`、`examples/register_mcp_server_to_nacos.py`、`tests/test_nacos_registration.py` |
| MCP Gateway 从 Nacos 发现 MCP Server | 已实现 `DiscoveryClient` 抽象、mock discovery、Nacos OpenAPI adapter，并通过本地 Docker Nacos 验证 | `src/mcp_gateway/discovery/**`、`tests/test_nacos_discovery.py`、`docker-compose.nacos.yml` |
| 形成统一 Tool Catalog | 已实现 Catalog 聚合、工具列表、provider 实例过滤 | `src/mcp_gateway/catalog/tool_catalog.py`、`tests/test_catalog_router.py` |
| 对上游提供工具发现与调用入口 | 已提供 `GET /api/v1/tools`、`GET /api/v1/tools/{toolName}/schema`、`POST /api/v1/tools/{toolName}/execute` | `src/mcp_gateway/api/tools.py`、`tests/test_api.py` |
| 支持知识库、审批、文档 Tool | 已实现 `knowledge.search`、`approval.create_task`、`document.generate` 三类 mock Tool | `src/mcp_gateway/examples/sample_metadata.py`、`src/mcp_gateway/client/mock_mcp_client.py` |
| 按工具名和健康状态路由 | 已实现 Router/Scheduler、健康实例过滤、主动健康检查 | `src/mcp_gateway/routing/router_scheduler.py`、`src/mcp_gateway/health/**` |
| MCP Server 不健康时不再转发新调用 | 已通过 Catalog provider 过滤和主动健康检查实现 | `tests/test_health_checker.py` |
| Nacos 短暂不可用时使用最后一次 Catalog | 已实现 Discovery 失败保留快照策略 | `src/mcp_gateway/runtime.py`、`tests/test_runtime_snapshot.py` |
| 鉴权、审计、限流和调用治理 | 已实现 YAML 权限、审计日志/JSONL 文件落地、基础 metrics 指标、Prometheus 告警规则样例、内存限流、内存熔断 | `src/mcp_gateway/policy/**`、`src/mcp_gateway/observability/audit.py`、`src/mcp_gateway/observability/metrics.py`、`deploy/prometheus/mcp-gateway-alerts.yml`、`src/mcp_gateway/routing/circuit_breaker.py` |
| Trace/requestId 与统一错误码 | 已实现统一响应 envelope、request/trace id 透传和错误码映射 | `src/mcp_gateway/api/response_envelope.py`、`src/mcp_gateway/observability/trace.py`、`src/mcp_gateway/domain/errors.py` |
| Catalog 管理与手动刷新 | 已实现 admin status 和 refresh 接口，并加 admin 权限保护 | `src/mcp_gateway/api/admin.py`、`tests/test_admin_api.py` |
| 无需手动触发的动态发现 | 已实现可选定时 Catalog refresh，支持周期性重拉 Discovery | `src/mcp_gateway/runtime.py`、`src/mcp_gateway/main.py`、`tests/test_runtime_snapshot.py` |
| schema 从配置中心读取 | 已实现可选 Nacos Config schema registry，支持缓存、namespace、group 和鉴权；本地 Docker Nacos 已发布 mock schema 并完成 `/schema` 与缺参校验验证 | `src/mcp_gateway/schema/schema_registry.py`、`src/mcp_gateway/examples/nacos_schema_config.py`、`examples/publish_schemas_to_nacos.py`、`tests/test_schema_registry.py`、`tests/test_nacos_schema_config.py` |

## 4. 未完全闭环项

| 项目 | 当前状态 | 影响 | 建议 |
| --- | --- | --- | --- |
| MCP Server 自动注册到真实 Nacos | 已提供 Python 注册 helper、生命周期封装、ephemeral 心跳和命令行示例，本地 Docker Nacos 已验证；尚未嵌入真实业务 MCP Server 生命周期 | 业务服务接入时仍需在启动/关闭钩子中调用注册/注销，非 Python 服务需补语言适配 | 在各业务 MCP Server 项目中集成 helper，或补 Java 版注册 helper |
| Nacos watch/订阅变更 | 当前 adapter 是按接口拉取，已支持手动 refresh 和可选定时 refresh，尚未实现 Nacos watch 推送 | 无法做到推送级实时感知，但可通过周期刷新满足测试环境动态发现 | 后续补 Nacos watch 机制 |
| 灰度发布 | 设计有灰度能力，MVP 尚未实现 labels/gray 策略过滤 | 灰度路由和按标签发布暂不可用 | 在 Router 中增加 label/gray rule 配置 |
| 租户级路由策略 | 当前权限校验支持 tenant allow，Router 尚未按 tenantMode 做复杂筛选 | 多租户专属实例场景需要扩展 | metadata 增加 tenant scope 后补 Router 过滤 |
| 生产级限流和熔断 | 已支持内存和 Redis 共享状态后端，并具备基础指标出口 | 多 Gateway 副本上线前仍需压测容量、恢复窗口和降级策略 | 基于 Redis 后端做生产压测，补充容量评估和告警阈值 |
| 完整观测闭环 | 当前已有 Prometheus 文本格式 `/metrics`、告警规则样例和 JSONL 文件审计落地；尚未接公司指标平台和审计中心 | 运维侧采集、留存和告警闭环不足 | 接入公司指标平台/审计中心，并根据生产压测校准阈值 |
| 真实业务系统对接 | 当前审批、文档、知识库均为 mock 响应 | 只能演示网关治理链路，不代表真实业务结果 | 后续分别接知识库、审批、文档业务服务 |

## 5. 额外实现项

以下内容超出首版 MVP 的最小要求，但与设计方向一致：

- Admin Catalog status/refresh 接口和 admin 权限保护。
- 工具 schema 查询接口和 Nacos Config schema registry 后端。
- Discovery 失败保留 Catalog 快照。
- 主动健康检查。
- 三类演示 Tool 的完整 mock 链路。
- 本地 Docker Nacos、示例 MCP Server 和 Nacos 专用 Gateway 配置。

这些扩展提升了可演示性和联调准备度，没有发现与需求冲突的行为。

## 6. 风险与影响

- 当前 Nacos adapter 和 Nacos Config schema registry 已通过本地 Docker Nacos 验证，公司测试/生产环境的鉴权、namespace/group、网络策略仍需要参数验证。
- 当前默认 mock discovery 会暴露三类工具；如果用于更严格的 MVP 演示，需要说明审批和文档为 mock。
- 进程内限流和熔断适合单实例或本地演示；多副本部署应使用 Redis 后端或迁移到基础设施层，并完成压测与告警阈值配置。
- `Tool Catalog` 在健康检查失败时仍保留工具描述但 provider 为空，这有利于目录可见性，但上游调用会得到 `MCP_SERVER_UNAVAILABLE`，需要在产品文案或接口说明中解释。

## 7. 建议后续动作

1. 进入外部 Nacos 测试环境联调，验证 serviceName、group、namespace、metadata 格式、鉴权和网络策略。
2. 将注册生命周期 helper 嵌入业务 MCP Server；如业务服务非 Python，补对应语言 helper 或复用服务自身 Nacos SDK。
3. 在测试环境开启 `catalog_refresh` 做动态发现验证，后续再补 Nacos watch 推送机制。
4. 将 `/metrics` 和 JSONL 审计文件接入统一可观测平台，并基于样例规则校准限流、熔断、健康状态和调用失败告警。
5. 在真实业务系统接入前，分别为知识库、审批、文档确认最终参数 schema 和响应 schema。

## 8. 审查结论

当前实现已覆盖需求文档中的核心目标：注册元数据约定、动态发现能力、Nacos Config schema 读取、统一工具目录、工具调用入口、健康剔除、权限审计限流和调用观测基础能力均已具备。本地 Docker Nacos 联调已闭环；未闭环项主要集中在公司测试/生产环境参数验证、生产级治理能力和真实业务系统对接，符合 MVP 阶段边界。
