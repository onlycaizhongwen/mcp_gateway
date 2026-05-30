# 项目状态

- 当前版本：v1
- 当前阶段：已计划
- 当前主题：mcp-gateway-nacos-discovery
- 说明：此文件用于记录需求、设计、计划、实现与追踪的主线状态。

## 需求索引

| 主题 | 需求文档 | 设计文档 | 计划文档 | Trace 文档 | 状态 |
| --- | --- | --- | --- | --- | --- |
| mcp-gateway-nacos-discovery | docs/codex/v1/requirements/mcp-gateway-nacos-discovery-requirements.md | docs/codex/v1/designs/mcp-gateway-nacos-discovery-design.md | docs/codex/v1/plans/mcp-gateway-nacos-discovery-plan.md | docs/codex/v1/trace/mcp-gateway-nacos-discovery-trace.md | 实现已验证 |

## 进度与状态

| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| 需求 | 已完成 | 已根据用户原始需求补充需求基线。 |
| 设计 | 已完成 | 已输出 MCP Server 自动注册 Nacos、MCP 网关动态发现与调度设计。 |
| 计划 | 已完成 | 已基于主设计和补充方案拆分 MVP 实施计划。 |
| 实现 | 进行中 | 已完成 Python/FastAPI MVP 骨架、mock discovery、Nacos discovery adapter、Tool Catalog、Router、HTTP API、三类演示 Tool、YAML 权限配置、工具 schema 查询/基础校验、可插拔 schema registry（内存默认，Nacos Config 可选）、官方 Python MCP SDK Streamable HTTP Client adapter、可插拔审计（日志默认，JSONL 文件可选）、Prometheus `/metrics` 基础指标、Catalog 管理接口、admin 权限保护、可插拔限流/熔断（内存默认，Redis 可选）、本地 Docker Redis 治理联调、可选主动健康检查、可选定时 Catalog 刷新、本地 Docker Nacos 注册/发现/Config schema/调用联调配置和示例 MCP Server。 |
| 追踪 | 已完成 | 已输出 trace 审查，核心 MVP 已闭环；本地 Nacos 注册、发现、Nacos Config schema、健康检查和 Streamable HTTP 调用已验证，本地 Redis 限流/熔断共享状态已验证，基础 metrics 出口和 JSONL 审计落地已具备，剩余项主要是公司测试/生产 Nacos 环境参数验证、生产压测/指标平台告警配置、审计中心接入和真实业务系统对接。 |

## 变更记录

- 2026-05-30：新增可插拔审计配置，默认保持日志输出，支持 `audit.mode=file` 写入 JSONL 审计文件；审计事件包含 trace/request、app/tenant、tool、结果码、耗时、路由实例和参数 key，不记录参数明文；当前全量测试 `74 passed`。
- 2026-05-29：新增 Prometheus 文本格式 `/metrics` 指标出口，记录工具调用总数、结果码、耗时汇总和 Catalog 刷新成功/快照/实例数指标；补充 API、运行时和 metrics 单元测试，当前全量测试 `69 passed`。
- 2026-05-29：将内存 schema registry 升级为可插拔后端，默认保留内存样例，新增 Nacos Config schema registry；`nacos://mcp-schemas/...` schema ref 可映射为 Nacos Config `dataId=...json`，并支持复用 Nacos endpoint、namespace、鉴权和超时配置。
- 2026-05-29：补齐本地 Docker Nacos Config schema mock 联调，新增 `examples/publish_schemas_to_nacos.py` 和 schema 发布 helper；已在本地 Nacos 中发布 mock schema，验证 Gateway `/schema` 从 Nacos Config 读取、缺参校验生效、工具调用经 Nacos discovery + 官方 SDK client 成功。
- 2026-05-29：将 Streamable HTTP client 从手写 JSON-RPC 调用替换为官方 Python MCP SDK adapter，锁定 `mcp==1.27.1`，通过 `streamable_http_client`、`ClientSession.initialize()` 和 `session.call_tool()` 调用下游 MCP Server；同步将本地示例 MCP Server 改为官方 FastMCP 实现，并完成 `56 passed` 与本地端到端烟测。
- 2026-05-29：完成本地 Docker Nacos 联调，新增 `docker-compose.nacos.yml`、`config/mcp-gateway-nacos-local.yaml` 和 `examples/mock_mcp_server.py`；修正 Nacos metadata 写入为 `metadata.mcp` JSON 字符串，并验证 Gateway 发现 `knowledge.search`、`providers=1`、Streamable HTTP `tools/call` 调用成功。
- 2026-05-29：升级限流和熔断为可插拔治理后端，默认保留内存实现，并新增 Redis 共享状态后端；限流使用 Redis token bucket，熔断使用 Redis 共享 failure/open 状态，支持多 Gateway 副本共享治理状态。
- 2026-05-29：新增本地 Docker Redis 联调配置和 `examples/redis_governance_smoke.py`，验证真实 Redis 后端中限流桶和熔断打开状态可跨两个 Gateway 治理对象共享。
- 2026-05-06：新增交付说明文档 `docs/codex/v1/delivery/mcp-gateway-mvp-delivery.md`，明确交付范围、运行方式、验证结果、对外交付口径、已知限制和待完成事项。
- 2026-05-06：新增 MCP Server 注册到 Nacos 的 Python 示例，包括可复用注册 helper、命令行示例和单元测试，并补充联调文档说明。
- 2026-05-06：新增可选定时 Catalog 刷新，通过 `catalog_refresh.enabled` 与 `interval_seconds` 配置周期性重拉 Discovery，支持无需手动 admin refresh 的动态发现。
- 2026-05-06：完成 trace 审查，输出 `docs/codex/v1/trace/mcp-gateway-nacos-discovery-trace.md`，确认 MCP Gateway MVP 核心链路已闭环，记录真实联调和生产化治理待办。
- 2026-05-06：完成演示工具扩展，新增 `approval.create_task` 和 `document.generate` 的 mock metadata、schema、权限配置、client 响应和 API 测试，形成知识库、审批、文档三类 Tool 演示链路。
- 2026-05-06：完成真实 Nacos 联调准备，新增 MCP Server 注册 metadata 模板、Nacos 联调说明、非法 metadata 跳过日志，以及 Discovery 失败保留最后一次 Catalog 快照策略。
- 2026-05-06：新增可选主动健康检查，Catalog 刷新时可基于 MCP Server `healthPath` 探活；Admin Catalog status 增加实例总数、健康实例数和不可用实例数。
- 2026-05-06：新增基础内存限流，按 `app_id + tenant_id + tool_name` 维度读取 `permissions.apps[].rate_limit` 配置执行 token bucket 限流，超过限制返回 `MCP_RATE_LIMITED`/429。
- 2026-05-06：补充下一阶段实施规划，建议优先进入基础限流与调用保护，随后推进主动健康检查、真实 Nacos 联调和审批/文档 Tool 演示链路。
- 2026-05-06：新增最小内存熔断器，支持按 MCP Server 实例统计下游失败、打开后路由跳过、恢复窗口后半开试探，并通过 `circuit_breaker` 配置控制。
- 2026-05-06：为 admin Catalog 管理接口新增最小权限保护，通过配置 `admin.allowed_app_ids` 与 `x-app-id` header 控制访问。
- 2026-05-06：新增 GatewayRuntime 和 Catalog 管理接口，支持查询 Catalog 状态与手动刷新 Discovery/Catalog。
- 2026-05-06：新增最小审计日志，记录工具调用 app、tenant、tool、route、耗时和结果码，仅记录参数 key，不落参数明文。
- 2026-05-06：新增 Streamable HTTP MCP Client adapter 骨架，配置开启后可向选中 MCP Server endpoint 发送 JSON-RPC `tools/call` 请求，默认仍使用 mock client；2026-05-29 已替换为官方 Python MCP SDK adapter。
- 2026-05-06：新增 Nacos Discovery OpenAPI 适配骨架，配置开启时可按 service_names 拉取 Nacos 实例并复用 metadata parser，默认仍使用 mock。
- 2026-05-06：新增工具 schema registry、`GET /api/v1/tools/{toolName}/schema` 接口和基于 inputSchema 的必填参数校验。
- 2026-05-06：新增 `config/mcp-gateway.yaml` 与配置加载模块，将 app/tool 权限从硬编码改为 YAML 配置。
- 2026-05-06：完成 Python/FastAPI MCP Gateway MVP 首版实现，包含 mock Nacos Discovery、Tool Catalog、Router、HTTP API、knowledge.search mock 和测试。
- 2026-05-06：确认 MCP Gateway MVP 使用 Python 3.12 + FastAPI，更新执行计划并进入实现阶段。
- 2026-05-06：新增 `docs/codex/v1/plans/mcp-gateway-nacos-discovery-plan.md`，完成 MCP Gateway MVP 执行计划拆分，当前阶段推进为已计划。
- 2026-05-06：修订 `MCP工具集成平台技术方案.md`，对齐主设计待确认项，统一 SDK 锁版、Streamable HTTP、HTTP 适配边界、工具命名、权限密钥、幂等和异步响应策略。
- 2026-04-29：重绘部署图，简化实例级连线，按业务调用、服务订阅、注册心跳三类主链路表达部署关系，并补充部署图说明。
- 2026-04-29：微调组件图标签位置和折线对齐，使“刷新目录”“发现服务”“工具调用”“注册/心跳”标注更工整。
- 2026-04-29：收敛组件图 Gateway 内部连线，移除绕线路径，保留更直观的模块依赖关系。
- 2026-04-29：检查并修正组件图语义，移除 Nacos Discovery 直连 Router 的误导关系，改为 Discovery 刷新 Tool Catalog，Router 查询 Tool Catalog。
- 2026-04-29：再次简化组件图，移除 MCP Server 实例级调用分支，仅保留调用、发现、注册三条主链路，并补充不展开实例分支的说明。
- 2026-04-29：修正组件图 MCP 调用链路，将多条 MCP Server 调用线合并为 MCP Server 集群入口，并说明路由只选择一个目标实例。
- 2026-04-29：重绘组件图为分层架构风格，并补充组件图文字说明与链路图例。
- 2026-04-29：优化组件图和部署图 SVG 连线，分离注册、订阅和调用路径，避免箭头重叠。
- 2026-04-29：新增 HTML 格式设计文档 `docs/codex/v1/designs/mcp-gateway-nacos-discovery-design.html`，用于直接浏览 UML 图片和设计内容。
- 2026-04-29：新增 UML SVG 图片文件，并在设计文档中增加图片引用，避免 Markdown 查看器不支持 Mermaid 时无法看图。
- 2026-04-29：补充 MCP 网关设计 UML 视图，包括组件图、部署图、注册发现时序图、工具调用时序图和核心类图。
- 2026-04-29：新增 `mcp-gateway-nacos-discovery` 主题需求基线与技术设计文档。
