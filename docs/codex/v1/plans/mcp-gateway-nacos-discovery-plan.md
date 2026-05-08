# MCP 网关 Nacos 服务发现执行计划

版本：v1  
主题：mcp-gateway-nacos-discovery  
需求文档：`docs/codex/v1/requirements/mcp-gateway-nacos-discovery-requirements.md`  
设计文档：`docs/codex/v1/designs/mcp-gateway-nacos-discovery-design.md`  
补充方案：`docs/codex/v1/designs/MCP工具集成平台技术方案.md`

## 1. 目标

将设计方案拆成可编码、可验证、可阶段交付的实施计划。首期目标是完成 MCP Gateway MVP：

- MCP Server 可注册服务实例与工具 metadata。
- MCP Gateway 可从 Nacos 发现 MCP Server。
- Gateway 可构建 Tool Catalog，并对外暴露工具列表。
- Gateway 可按工具名路由到一个可用 MCP Server 实例。
- Gateway 可提供 HTTP API 适配入口，完成一次 `knowledge.search` 端到端调用。

## 2. 实施边界

### 2.1 MVP 范围

- Gateway 基础工程骨架。
- Nacos Discovery 抽象和本地模拟实现。
- MCP Server Instance / Tool Descriptor / Tool Route 核心模型。
- Tool Catalog 聚合、查询和冲突检测。
- Router / Scheduler 基础实现。
- HTTP API 适配接口：
  - `GET /api/v1/tools`
  - `POST /api/v1/tools/{toolName}/execute`
- `knowledge.search` 示例 MCP Server 或 mock provider。
- 基础鉴权占位、traceId/requestId 透传、统一错误码。
- 单元测试和最小集成测试。

### 2.2 非 MVP 范围

- 真实知识库、审批、文档业务系统对接。
- 完整生产 Nacos 账号、白名单和 K8s 部署。
- 完整权限中心、KMS/Vault 密钥对接。
- 灰度、复杂限流、完整审计链路。
- 原生 MCP Client 接入入口。
- `approval.create_task` 和 `document.generate` 的真实业务实现。

## 3. 前置条件

| 条件 | 状态 | 处理建议 |
| --- | --- | --- |
| Gateway 技术栈 | 已确认 | 使用 Python 3.12 + FastAPI 实现 MCP Gateway MVP。 |
| Nacos 环境 | 待确认 | MVP 可先做 Nacos Client 接口 + 本地 mock，避免阻塞工程骨架。 |
| SDK 版本 | 待确认 | 编码依赖文件必须锁定具体版本，不使用 `latest`。 |
| HTTP API 契约 | 已有草案 | MVP 可按补充方案接口实现。 |
| 工具命名 | 已明确 | 使用 `knowledge.search`、`approval.create_task`、`document.generate`。 |
| 密钥系统 | 待确认 | MVP 不落真实密钥，只保留 `credential_ref` 模型。 |

## 4. 推荐工程结构

本项目已确认选择 Python/FastAPI，建议结构如下：

```text
src/mcp_gateway/
  main.py
  config/
    gateway_config.py
  domain/
    models.py
    errors.py
  discovery/
    base.py
    mock_discovery.py
    metadata_parser.py
  catalog/
    tool_catalog.py
  routing/
    router_scheduler.py
  api/
    tools.py
    response_envelope.py
  client/
    base.py
    mock_mcp_client.py
  policy/
    auth_context.py
    policy_checker.py
  observability/
    trace.py
  examples/
    sample_metadata.py
tests/
  catalog/
  routing/
  discovery/
  api/
```

后续如果补 Python MCP SDK 或真实 Nacos Client，也应保持同等模块边界：

- domain
- discovery
- catalog
- routing
- api
- client
- policy
- observability

## 5. 实施步骤

### 阶段 0：技术栈确认

1. 确认 Gateway 技术栈。
2. 确认是否允许引入 MCP 官方 SDK。
3. 锁定 SDK、HTTP 框架、测试框架版本。
4. 确认本地开发运行方式。

检查点：

- 若技术栈未确认，不进入真实编码，只能维护计划和接口设计。

### 阶段 1：工程骨架与核心模型

1. 初始化工程骨架和基础配置。
2. 定义核心模型：
   - `McpServerInstance`
   - `ToolDescriptor`
   - `ToolRoute`
   - `GatewayError`
3. 定义统一响应 envelope。
4. 定义错误码：
   - `MCP_TOOL_NOT_FOUND`
   - `MCP_TOOL_DISABLED`
   - `MCP_TOOL_PERMISSION_DENIED`
   - `MCP_TOOL_VALIDATION_FAILED`
   - `MCP_SERVER_UNAVAILABLE`
   - `MCP_TOOL_EXECUTION_FAILED`

验证：

- 模型序列化/反序列化测试。
- 错误码映射测试。

### 阶段 2：Nacos Discovery 与 metadata 解析

1. 定义 `DiscoveryClient` 接口。
2. 实现 `MockDiscoveryClient`，用于本地测试。
3. 实现 metadata parser，支持补充方案中的 metadata 格式。
4. 校验字段：
   - `metadataVersion`
   - `mcpProtocolVersion`
   - `transport`
   - `endpoint`
   - `tools[].name`
   - `tools[].version`
   - `tools[].inputSchemaRef`
   - `tools[].outputSchemaRef`
5. 预留真实 Nacos client 适配层。

验证：

- 合法 metadata 可解析。
- 非法 metadata 被跳过并产生错误记录。
- disabled tool 不进入可调用目录。

### 阶段 3：Tool Catalog

1. 实现 Catalog snapshot。
2. 支持全量刷新和原子替换。
3. 支持按工具名、版本、domain、tenant 查询。
4. 支持同名冲突检测。
5. 支持实例健康状态过滤。

验证：

- 新实例加入后工具可见。
- 实例下线后工具不可路由。
- 同名同版本冲突进入冲突状态。
- Catalog 刷新不产生半更新状态。

### 阶段 4：Router / Scheduler

1. 实现候选实例过滤：
   - toolName
   - version
   - enabled
   - healthy
   - tenantMode
2. 实现基础调度策略：
   - MVP 使用加权轮询或简单轮询。
3. 输出 `ToolRoute`。
4. 记录 routeReason。

验证：

- 健康实例优先。
- 不健康实例不被选择。
- 无可用实例返回 `MCP_SERVER_UNAVAILABLE`。
- 多实例轮询行为可预测。

### 阶段 5：HTTP API 适配入口

1. 实现 `GET /api/v1/tools`。
2. 实现 `POST /api/v1/tools/{toolName}/execute`。
3. 支持统一上下文：
   - `tenant_id`
   - `app_id`
   - `user`
   - `trace_id`
   - `request_id`
4. 接入基础 policy checker。
5. 调用 `McpClient` 执行工具。

验证：

- 可查询工具列表。
- 有权限工具可调用。
- 未授权工具返回 `MCP_TOOL_PERMISSION_DENIED`。
- 未知工具返回 `MCP_TOOL_NOT_FOUND`。
- 响应包含 `traceId` 和 `requestId`。

### 阶段 6：MCP Client 与 knowledge.search 示例

1. 定义 `McpClient` 接口。
2. MVP 先实现 `MockMcpClient` 或本地示例 provider。
3. 实现 `knowledge.search` 示例响应。
4. 预留 Streamable HTTP MCP Client 适配层。

验证：

- `knowledge.search` 可端到端返回结构化结果。
- 下游异常可映射为统一错误码。
- 超时可返回 `MCP_TOOL_DOWNSTREAM_TIMEOUT`。

### 阶段 7：最小观测与日志

1. 生成或透传 `traceId`、`requestId`。
2. 记录工具调用日志：
   - appId
   - tenantId
   - toolName
   - route instance
   - duration
   - result code
3. 敏感参数只记录摘要，不记录明文。

验证：

- 日志可串联一次工具调用。
- 不输出 app secret、token、敏感业务参数。

## 6. 验证清单

| 场景 | 验证方式 | 期望 |
| --- | --- | --- |
| 服务注册 metadata 解析 | 单元测试 | 合法数据进入 Catalog。 |
| 工具发现 | API 测试 | `GET /api/v1/tools` 返回 `knowledge.search`。 |
| 工具调用 | API 测试 | `POST /api/v1/tools/knowledge.search/execute` 返回答案。 |
| 无权限调用 | API 测试 | 返回 `MCP_TOOL_PERMISSION_DENIED`。 |
| 未知工具 | API 测试 | 返回 `MCP_TOOL_NOT_FOUND`。 |
| 实例不健康 | 单元/集成测试 | Router 不选择该实例。 |
| Nacos 不可用 | mock 测试 | 使用最后一次 Catalog 或返回明确错误。 |
| metadata 非法 | 单元测试 | 跳过非法工具并记录错误。 |

## 7. 风险与回滚

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 技术栈未确认 | 编码返工 | 先确认技术栈，或先产出接口和测试用例。 |
| Nacos 环境不可用 | 集成阻塞 | MVP 使用 mock discovery，真实 Nacos 适配后置。 |
| SDK 版本变化 | 编译或协议不兼容 | 锁定版本，升级走兼容测试。 |
| Tool metadata 不规范 | Catalog 污染 | parser 严格校验，非法工具不暴露。 |
| 权限模型不完整 | 越权风险 | MVP 默认拒绝，只有明确 allow 的工具可调用。 |
| 下游工具超时 | 调用堆积 | 设置默认超时和错误码，后续补熔断。 |

回滚策略：

- HTTP API 新入口可通过配置关闭。
- Catalog 可回退到最后一次成功快照。
- 新 MCP Server 可从 Nacos 下线或禁用 metadata `enabled=false`。
- 工具级异常可通过权限配置或 metadata 暂停暴露。

## 8. 编码前确认点

进入编码前至少确认以下内容：

1. Gateway 技术栈：Python/FastAPI。
2. 是否允许 MVP 使用 mock Nacos，真实 Nacos 适配后续接入。
3. HTTP API 路径是否采用 `/api/v1/tools`。
4. MVP 是否只实现 `knowledge.search` 示例。
5. SDK 版本锁定策略是否接受候选版本。

如果以上无法一次性确认，建议先编码与语言无强绑定的部分：核心模型、metadata parser、Catalog 和 Router 测试用例。

## 9. 交付顺序建议

1. Plan 文档评审。
2. 技术栈确认。
3. 工程骨架与核心模型。
4. Mock Discovery + Metadata Parser。
5. Tool Catalog + Router。
6. HTTP API。
7. `knowledge.search` 示例链路。
8. 最小测试与演示。
9. 接入真实 Nacos。
10. 进入权限、审计、熔断和后续工具扩展。

## 10. 当前完成情况

截至 2026-05-06，MVP 已完成以下能力：

- Python/FastAPI 工程骨架、统一响应和错误码。
- Mock Discovery、metadata parser、Nacos OpenAPI Discovery adapter 骨架。
- Tool Catalog、Router/Scheduler、工具列表与工具调用 API。
- `knowledge.search` mock 端到端调用。
- YAML 权限配置、工具 schema 查询和必填参数校验。
- Streamable HTTP MCP Client adapter 骨架。
- 最小审计日志、Catalog 管理接口、Admin 权限保护。
- 最小内存熔断，支持下游失败后实例级隔离。
- 基础内存限流，支持按 app、tenant、tool 维度限制调用频率。
- 可选主动健康检查，Catalog 刷新时可基于 MCP Server `healthPath` 探活，并在 Admin status 暴露实例健康统计。
- 可选定时 Catalog 刷新，支持无需手动 admin refresh 的周期性动态发现。
- 真实 Nacos 联调准备，包括注册 metadata 模板、联调说明、非法 metadata 跳过日志、Discovery 失败保留快照策略。
- 演示工具扩展，支持 `knowledge.search`、`approval.create_task`、`document.generate` 三类 Tool 的 mock 端到端调用。
- `python -m pytest` 已通过，当前测试集 49 passed。

## 11. 下一阶段规划

下一阶段目标：把当前 MVP 从“本地可跑通”推进到“可联调、可观测、可控流量”的预集成版本。

### 阶段 8：基础限流与调用保护

目标：补齐工具调用入口的第一层流量保护，避免单个 app 或 tenant 打爆 MCP Server。

状态：已完成。

实施项：

1. 已新增轻量内存限流器，按 `app_id + tenant_id + tool_name` 维度计数。
2. 已读取现有 `permissions.apps[].rate_limit.qps/burst` 配置。
3. 已在工具调用路由前执行限流校验。
4. 已新增错误码 `MCP_RATE_LIMITED`，HTTP 状态码使用 429。
5. 已通过审计日志记录限流拒绝结果，不记录参数值。

验证：

- 同一 app 连续调用超过 burst 后返回 429。
- 不同 app、不同 tenant 的限流桶互不影响。
- 未配置限流时不影响现有调用。
- `python -m pytest` 通过，35 passed。

### 阶段 9：主动健康检查与 Catalog 状态增强

目标：让 Gateway 不只依赖 Nacos `healthy` 字段，也能主动探测 MCP Server 健康状态。

状态：已完成。

实施项：

1. 已新增 `HealthChecker` 抽象，支持 no-op 与 HTTP `healthPath` 探活。
2. Catalog refresh 时已可选执行健康探测，默认关闭以兼容本地 mock 模式。
3. Admin status 已返回实例数、健康实例数、不可用实例数和工具数。
4. 探活失败实例不会进入 Router 的 provider 候选集，工具描述仍可保留用于目录可见性。

验证：

- 健康接口失败时实例不被 Router 选择。
- Admin status 能看出不可用实例。
- mock 模式不依赖真实网络即可测试。
- `python -m pytest` 通过，38 passed。

### 阶段 10：真实 Nacos 联调准备

目标：让 Gateway 能接真实 Nacos 环境做服务发现联调。

状态：已完成。

实施项：

1. 已在联调说明中明确 Nacos namespace、group、serviceName、鉴权方式配置位置。
2. 已固化 MCP Server metadata 样例，补充注册模板 `mcp-server-nacos-registration-template.json`。
3. 已增加 Nacos adapter 非法 metadata 跳过日志，并补充 metadata JSON 字符串解析测试。
4. 已增加“发现失败时保留最后一次 Catalog 快照”的策略。
5. 已输出本地/测试环境联调说明 `mcp-gateway-nacos-integration-guide.md`。

验证：

- Nacos 返回真实实例时可进入 Catalog。
- Nacos 短暂不可用时不清空已有 Catalog。
- metadata 缺字段或格式错误时只跳过异常实例。
- `python -m pytest` 通过，41 passed。

### 阶段 11：演示工具扩展

目标：在 `knowledge.search` 之外补齐审批、文档两个 Tool 的可演示链路。

状态：已完成。

实施项：

1. 已新增 `approval.create_task` mock metadata、schema 和 client 响应。
2. 已新增 `document.generate` mock metadata、schema 和 client 响应。
3. 已补权限配置样例，`internal-ai-agent` 可调用三类工具，`demo-app` 仍只允许 `knowledge.search`。
4. 已补 API 测试和 README 调用示例。

验证：

- 三类工具均可查询、查 schema、执行。
- 未授权 app 调用新增工具会被拒绝。
- 各工具的必填参数校验生效。
- `python -m pytest` 通过，47 passed。

## 12. 推荐执行顺序

阶段 8、阶段 9、阶段 10 和阶段 11 已完成。建议下一轮进入 trace 审查，核对 requirements、design、plan 与实现是否闭环。

原因：

- 当前 Gateway 已具备权限、审计、熔断、限流、主动健康检查五个基本治理能力。
- Nacos 联调所需的注册模板、联调说明和失败快照策略已补齐。
- Gateway 已从单一 `knowledge.search` 示例扩展为知识库、审批、文档三类工具的完整演示平台。
- 按项目规则，当前主题已经完成主要实现和验证，应补一版 trace 审查文档。
