# MCP 工具集成平台技术方案

版本：1.1  
日期：2026-05-06  
关联文档：`docs/codex/v1/designs/mcp-gateway-nacos-discovery-design.md`  
定位：对主设计文档“待确认项”的补充和落地决策建议

---

## 1. 概述

### 1.1 背景

明源云 AI 升级项目需要基于 MCP 协议建设统一工具层，将知识库、审批、文档生成等业务能力封装为可被 AI 应用调用的 Tool。主设计文档已经明确 MCP Server 自动注册到 Nacos、MCP Gateway 动态发现与调度的总体方案。

本文补充回答主设计中的待确认项：

- MCP Server 的主要技术栈与 MCP SDK 版本。
- Nacos 环境的 namespace、group、鉴权方式和网络连通策略。
- 上游 AI 应用直接使用 MCP 协议，还是通过 HTTP API 间接调用。
- 工具级权限模型按租户、角色、用户还是应用维度控制。
- 知识库、审批、文档三个首批 Tool 的名称、参数 schema 和响应 schema。

### 1.2 总体结论

| 待确认项 | 建议结论 |
| --- | --- |
| 技术栈 | 网关优先按项目主技术栈实现；MCP Server 可按业务团队能力选择 TypeScript 或 Python。 |
| MCP SDK | 禁止使用 `latest` 漂移版本；生产锁定官方 v1.x 稳定线，alpha/beta 版本仅用于验证环境。 |
| 远程传输 | 网关到 MCP Server 优先使用 Streamable HTTP；SSE 仅用于兼容历史实现；Stdio 仅用于本地进程型工具。 |
| 上游接入 | 第一阶段在 MCP Gateway 内提供 HTTP API 适配入口；第二阶段再开放原生 MCP Client 接入。 |
| 注册发现 | MCP Server 向 Nacos 注册实例和轻量 metadata，大型 schema 通过 `schemaRef` 外挂。 |
| 权限模型 | 应用级准入 + 租户/用户上下文 + 工具级策略 + 工具内部业务权限校验。 |
| 首批工具命名 | 统一采用领域前缀命名：`knowledge.search`、`approval.create_task`、`document.generate`。 |

---

## 2. MCP Server 技术选型与版本

### 2.1 技术栈选择

| 组件 | 建议 | 说明 |
| --- | --- | --- |
| MCP Gateway | 跟随项目主技术栈 | 网关负责注册发现、目录聚合、路由、鉴权和审计，应优先与现有服务治理体系一致。 |
| MCP Server | TypeScript 或 Python | 官方 SDK 对 TypeScript、Python 支持成熟，适合快速封装工具服务。 |
| 部署方式 | Docker / K8s | 与现有环境保持一致，便于健康检查、扩缩容和灰度。 |
| 传输协议 | Streamable HTTP | 适合远程服务化 MCP Server；支持统一 `/mcp` endpoint。 |

### 2.2 SDK 锁版策略

生产环境不使用“最新稳定版”这类模糊描述，必须在依赖文件中锁定明确版本。

| SDK | 建议策略 | 当前建议 |
| --- | --- | --- |
| TypeScript SDK | 使用官方 `@modelcontextprotocol/sdk` v1.x 稳定线 | 评审时锁定 v1.x 明确版本；候选为 `1.29.x`，禁止直接使用 v2 alpha。 |
| Python SDK | 使用官方 `mcp` v1.x 稳定线 | 评审时锁定 v1.x 明确版本；候选为 `1.27.x`。 |
| 协议版本 | 明确注册并兼容协商 | 首期按 `2025-03-26` 或团队确认版本注册；后续升级需走兼容评审。 |

版本治理要求：

- `package.json` / `requirements.txt` / lock 文件必须固定版本。
- SDK 升级必须先在测试环境验证工具列表、工具调用、错误码、流式响应和连接恢复。
- MCP Server 注册到 Nacos 的 metadata 中必须包含 `mcpProtocolVersion`、`serverVersion`、`metadataVersion`。
- alpha、beta、rc 版本不得进入生产依赖。

参考来源：

- MCP 官方 SDK 列表：https://modelcontextprotocol.io/docs/sdk
- MCP TypeScript SDK：https://github.com/modelcontextprotocol/typescript-sdk
- MCP Python SDK：https://github.com/modelcontextprotocol/python-sdk

### 2.3 传输协议决策

主链路采用：

```text
AI 应用
  -> MCP Gateway HTTP API 适配入口 或 MCP 原生入口
  -> MCP Gateway 内部路由
  -> MCP Server Streamable HTTP endpoint: /mcp
```

说明：

- Streamable HTTP 是远程 MCP Server 的优先方案。
- SSE 可作为旧版本兼容，不作为新增服务默认方案。
- Stdio 适合本地子进程工具，不适合网关到远程 MCP Server 的服务化调用。
- WebSocket 不作为本项目 MCP 主传输方案，避免与官方标准传输不一致。

参考来源：

- MCP 2025-03-26 Transports：https://modelcontextprotocol.io/specification/2025-03-26/basic/transports
- MCP 2025-03-26 Changelog：https://modelcontextprotocol.io/specification/2025-03-26/changelog

---

## 3. Nacos 环境配置

### 3.1 待基础设施确认项

```yaml
nacos:
  endpoint: "待确认"
  namespace:
    dev: "待确认"
    test: "待确认"
    prod: "待确认"
  group:
    mcp_server: "MCP_SERVER_GROUP"
    mcp_config: "MCP_CONFIG_GROUP"
  authentication:
    type: "待确认"       # username_password / access_key / ldap / none
    credential_ref: "待确认" # 指向密钥系统，不在本文档或 Nacos 明文保存
  network:
    access_from: "K8s集群 / VM / 具体网段，待确认"
    vpn_required: "待确认"
    white_list: "待确认"
  permission:
    gateway_read: true
    mcp_server_register: true
    config_read: true
    config_write: "仅配置管理流程允许"
```

### 3.2 Nacos 数据分层

| 数据类型 | 存放位置 | 说明 |
| --- | --- | --- |
| 服务实例 | Nacos Service Registry | MCP Server 的 host、port、weight、healthy、metadata。 |
| 轻量工具 metadata | Nacos instance metadata | 工具名、版本、domain、transport、endpoint、schemaRef、labels。 |
| 大型 schema | Nacos Config / 对象存储 / 元数据服务 | 不建议塞入 instance metadata。 |
| 权限策略 | Nacos Config 或权限配置中心 | 只放策略，不放明文密钥。 |
| 应用密钥 | KMS / Vault / K8s Secret / 公司统一密钥系统 | Nacos 中只保留 `credential_ref`。 |

### 3.3 MCP Server 注册 metadata 建议

```json
{
  "metadataVersion": "1.0",
  "mcpProtocolVersion": "2025-03-26",
  "transport": "streamable-http",
  "endpoint": "/mcp",
  "healthPath": "/health",
  "domain": "knowledge",
  "serverVersion": "1.0.0",
  "toolSetVersion": "1.0.0",
  "tenantMode": "shared",
  "authType": "gateway-token",
  "enabled": true,
  "labels": ["prod", "stable"],
  "tools": [
    {
      "name": "knowledge.search",
      "version": "1.0.0",
      "description": "Search enterprise knowledge base",
      "inputSchemaRef": "nacos://mcp-schemas/knowledge.search/1.0.0/input",
      "outputSchemaRef": "nacos://mcp-schemas/knowledge.search/1.0.0/output",
      "readOnly": true,
      "destructive": false,
      "idempotent": true,
      "enabled": true
    }
  ]
}
```

### 3.4 行动项

1. 向基础设施团队确认 endpoint、namespace、group、鉴权方式和白名单。
2. 验证 Gateway 与 MCP Server 所在网络到 Nacos 的连通性。
3. 明确 Nacos 读写权限边界，生产环境禁止服务随意写配置。
4. 确认 schema 存储位置和 schemaRef 命名规范。

---

## 4. 上游 AI 应用集成方案

### 4.1 阶段化策略

第一阶段推荐在 MCP Gateway 内提供 HTTP API 适配入口，降低上游 AI 应用改造成本；第二阶段再开放原生 MCP Client 接入。注意：HTTP 适配是 MCP Gateway 的接入能力，不建议另起一个与 MCP Gateway 重叠的独立网关，除非组织架构明确需要拆分部署。

```text
阶段一：
AI 应用
  -> MCP Gateway HTTP API
  -> Tool Catalog / Router / Policy
  -> MCP Server Streamable HTTP

阶段二：
AI 应用 MCP Client
  -> MCP Gateway MCP endpoint
  -> Tool Catalog / Router / Policy
  -> MCP Server Streamable HTTP
```

### 4.2 HTTP API 适配接口

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/tools` | GET | 查询当前应用、租户可见工具列表。 |
| `/api/v1/tools/{toolName}/execute` | POST | 执行工具调用。 |
| `/api/v1/tool-tasks/{taskId}` | GET | 查询异步工具任务状态。 |
| `/api/v1/tool-tasks/{taskId}/result` | GET | 获取异步工具结果。 |

统一响应 envelope：

```json
{
  "code": "0",
  "message": "success",
  "data": {},
  "traceId": "trace-xxx",
  "requestId": "req-xxx"
}
```

错误响应：

```json
{
  "code": "MCP_TOOL_PERMISSION_DENIED",
  "message": "应用无权限调用该工具",
  "data": null,
  "traceId": "trace-xxx",
  "requestId": "req-xxx"
}
```

### 4.3 原生 MCP 接入

原生 MCP 接入适用场景：

- 上游 AI 应用已经具备 MCP Client 能力。
- 需要流式响应、进度通知或更完整的 MCP 能力。
- 调用频率高，希望减少 HTTP 适配层语义转换。

原生 MCP 接入仍应经过 MCP Gateway，而不是直接连接后端 MCP Server，以保证权限、审计、限流和路由治理一致。

---

## 5. 权限模型设计

### 5.1 权限原则

- 最小权限：应用只能看到和调用授权工具。
- 分层校验：应用级准入、租户/用户上下文、工具级策略、业务系统内部权限。
- 密钥不落 Nacos：Nacos 只存策略和密钥引用。
- 全链路审计：工具发现、工具调用、失败原因和业务结果均可追踪。

### 5.2 权限分层

| 层级 | 负责方 | 校验内容 |
| --- | --- | --- |
| 应用认证 | MCP Gateway | appId、签名、token、调用来源。 |
| 租户隔离 | MCP Gateway | tenantId、环境、应用归属租户。 |
| 工具授权 | MCP Gateway | allowedTools、工具版本、调用配额、限流策略。 |
| 用户上下文 | MCP Gateway / MCP Server | userId、roles、orgId、数据范围。 |
| 业务权限 | MCP Server / 下游业务系统 | 审批权限、文档模板权限、知识库范围权限。 |

### 5.3 权限配置示例

```yaml
permissions:
  apps:
    - app_id: "internal-ai-agent"
      credential_ref: "kms://mcp/apps/internal-ai-agent"
      tenants: ["tenant-a", "tenant-b"]
      allowed_tools:
        - "knowledge.search"
        - "approval.create_task"
        - "document.generate"
      rate_limit:
        qps: 20
        burst: 50

  tools:
    knowledge.search:
      requires_user_context: true
      read_only: true
      max_query_length: 1000
      allowed_knowledge_scopes: ["hr", "project", "policy"]

    approval.create_task:
      requires_user_context: true
      destructive: true
      idempotency_required: true
      allowed_approval_types: ["leave", "expense", "document"]

    document.generate:
      requires_user_context: true
      async_supported: true
      allowed_formats: ["pdf", "docx", "md", "html"]
```

### 5.4 权限校验流程

```python
def tool_execution_flow(app_context, user_context, tool_name, params):
    # 1. 应用级认证与工具白名单
    if not is_app_allowed(app_context.app_id, app_context.tenant_id, tool_name):
        raise PermissionError("应用无此工具权限")

    # 2. 工具级策略
    tool_policy = get_tool_policy(tool_name)
    if tool_policy.requires_user_context and not user_context.authenticated:
        raise AuthenticationError("需要用户身份")

    # 3. 幂等要求
    if tool_policy.idempotency_required and not params.get("idempotency_key"):
        raise ValidationError("缺少幂等键")

    # 4. 业务权限
    check_business_permission(user_context, tool_name, params)

    # 5. 执行并审计
    return execute_tool(tool_name, params, app_context, user_context)
```

---

## 6. 首批工具定义

### 6.1 命名规范

MCP Tool Catalog 统一采用领域前缀命名：

| 工具 | MCP Tool 名称 | HTTP alias |
| --- | --- | --- |
| 知识库查询 | `knowledge.search` | `query_knowledge_base` |
| 创建审批任务 | `approval.create_task` | `create_approval_task` |
| 生成文档 | `document.generate` | `generate_document` |

说明：

- MCP 内部和 Nacos metadata 统一使用领域前缀命名。
- HTTP API 可保留 alias 方便旧系统接入，但需映射到 MCP Tool 名称。
- 工具版本与 schema 版本必须显式管理。

### 6.2 通用调用上下文

所有工具调用都应携带统一上下文：

```json
{
  "tenant_id": "tenant-a",
  "app_id": "internal-ai-agent",
  "user": {
    "user_id": "zhangsan",
    "roles": ["employee"],
    "org_id": "tech"
  },
  "trace_id": "trace-xxx",
  "request_id": "req-xxx"
}
```

### 6.3 工具一：知识库查询

```json
{
  "name": "knowledge.search",
  "version": "1.0.0",
  "description": "根据自然语言问题查询知识库，返回最相关的知识片段",
  "annotations": {
    "readOnly": true,
    "destructive": false,
    "idempotent": true
  },
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "自然语言查询问题",
        "maxLength": 1000
      },
      "top_k": {
        "type": "integer",
        "description": "返回结果数量，默认3",
        "default": 3,
        "minimum": 1,
        "maximum": 10
      },
      "threshold": {
        "type": "number",
        "description": "相似度阈值，范围0到1",
        "default": 0.7,
        "minimum": 0,
        "maximum": 1
      },
      "scope": {
        "type": "array",
        "items": { "type": "string" },
        "description": "知识范围，可选"
      }
    },
    "required": ["query"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "answer": { "type": "string" },
      "references": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "title": { "type": "string" },
            "source": { "type": "string" },
            "score": { "type": "number" }
          }
        }
      }
    },
    "required": ["answer"]
  }
}
```

### 6.4 工具二：创建审批任务

审批创建是有副作用工具，必须支持幂等键，避免网关重试导致重复创建。

```json
{
  "name": "approval.create_task",
  "version": "1.0.0",
  "description": "创建审批流程任务，支持请假、报销、用印等审批类型",
  "annotations": {
    "readOnly": false,
    "destructive": true,
    "idempotent": true
  },
  "inputSchema": {
    "type": "object",
    "properties": {
      "idempotency_key": {
        "type": "string",
        "description": "幂等键，调用方生成，同一业务请求必须保持一致"
      },
      "approval_type": {
        "type": "string",
        "enum": ["leave", "expense", "document"]
      },
      "title": {
        "type": "string",
        "maxLength": 200
      },
      "content": {
        "type": "object"
      },
      "approvers": {
        "type": "array",
        "items": { "type": "string" },
        "minItems": 1
      },
      "priority": {
        "type": "string",
        "enum": ["low", "normal", "high", "urgent"],
        "default": "normal"
      },
      "dry_run": {
        "type": "boolean",
        "description": "仅校验不创建，用于高风险调用前确认",
        "default": false
      }
    },
    "required": ["idempotency_key", "approval_type", "title", "content", "approvers"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "approval_id": { "type": "string" },
      "status": { "type": "string" },
      "url": { "type": "string" },
      "duplicated": { "type": "boolean" }
    },
    "required": ["approval_id", "status"]
  }
}
```

### 6.5 工具三：生成文档

文档生成可能耗时较长，默认支持异步响应。

```json
{
  "name": "document.generate",
  "version": "1.0.0",
  "description": "根据模板和数据生成结构化文档",
  "annotations": {
    "readOnly": false,
    "destructive": false,
    "idempotent": true,
    "async": true
  },
  "inputSchema": {
    "type": "object",
    "properties": {
      "idempotency_key": {
        "type": "string"
      },
      "template_id": {
        "type": "string"
      },
      "data": {
        "type": "object"
      },
      "format": {
        "type": "string",
        "enum": ["pdf", "docx", "md", "html"],
        "default": "pdf"
      },
      "watermark": {
        "type": "string"
      },
      "callback_url": {
        "type": "string",
        "description": "可选，异步完成后回调"
      }
    },
    "required": ["idempotency_key", "template_id", "data"]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "task_id": { "type": "string" },
      "status": { "type": "string" },
      "status_url": { "type": "string" },
      "result_url": { "type": "string" },
      "estimated_completion": { "type": "string" }
    },
    "required": ["task_id", "status"]
  }
}
```

### 6.6 错误码建议

| 错误码 | 场景 |
| --- | --- |
| `MCP_TOOL_NOT_FOUND` | 工具不存在或未暴露。 |
| `MCP_TOOL_DISABLED` | 工具被禁用。 |
| `MCP_TOOL_PERMISSION_DENIED` | 应用、租户或用户无权限。 |
| `MCP_TOOL_VALIDATION_FAILED` | 参数校验失败。 |
| `MCP_TOOL_IDEMPOTENCY_REQUIRED` | 缺少幂等键。 |
| `MCP_TOOL_DOWNSTREAM_TIMEOUT` | 下游业务系统超时。 |
| `MCP_TOOL_EXECUTION_FAILED` | 工具执行失败。 |
| `MCP_SERVER_UNAVAILABLE` | 无可用 MCP Server 实例。 |

---

## 7. 实施路线图

### 7.1 MVP 阶段：注册发现与知识库工具

目标：验证主链路可用。

- 确认 Nacos 环境与权限。
- 搭建 MCP Gateway 基础骨架。
- 实现 MCP Server 注册与 metadata 解析。
- 实现 Tool Catalog 聚合与查询。
- 实现 `knowledge.search` 工具。
- 提供 HTTP API 适配入口。
- 完成一次端到端调用验证。

### 7.2 第二阶段：审批、文档与权限治理

- 实现 `approval.create_task`，补齐幂等和 dry_run。
- 实现 `document.generate`，补齐异步任务状态查询。
- 实现应用级、租户级、工具级权限策略。
- 接入审计日志、指标和 Trace。
- 增加限流、熔断、超时和重试策略。

### 7.3 第三阶段：生产就绪

- 完成压测和容量评估。
- 完成灰度发布和回滚策略。
- 完成 Nacos 不可用、本地缓存降级、实例异常剔除测试。
- 完成安全评审，确认密钥、审计、脱敏和权限配置。
- 完成接入文档和运维手册。

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| MCP 协议和 SDK 演进较快 | 兼容风险 | 锁定 SDK 版本，metadata 注册协议版本，升级前做兼容测试。 |
| HTTP 适配与原生 MCP 边界不清 | 架构重复 | 明确 HTTP 适配是 MCP Gateway 接入层能力。 |
| Nacos metadata 过大 | 注册中心性能和稳定性风险 | 大型 schema 外挂，通过 schemaRef 引用。 |
| 审批类工具重复创建 | 业务事故 | 强制 idempotency_key，网关和工具侧共同校验。 |
| 密钥落入配置中心 | 安全风险 | Nacos 只存 credential_ref，密钥放 KMS/Vault/K8s Secret。 |
| 工具权限配置错误 | 越权调用 | 分层权限、默认拒绝、配置审计、灰度发布。 |

---

## 9. 待评审清单

| 项目 | 负责人 | 状态 |
| --- | --- | --- |
| 确认 MCP Gateway 技术栈 | 待定 | 待确认 |
| 锁定 TypeScript / Python SDK 版本 | 待定 | 待确认 |
| 确认 Nacos endpoint、namespace、group、鉴权和白名单 | 基础设施团队 | 待确认 |
| 确认 HTTP API 适配接口 | 网关负责人 / AI 应用负责人 | 待确认 |
| 确认权限配置格式和密钥系统 | 安全 / 平台团队 | 待确认 |
| 评审首批三个工具 schema | 业务系统负责人 | 待确认 |
| 确认审批和文档工具异步/幂等策略 | 业务系统负责人 | 待确认 |

---

## 10. 参考资料

- MCP 官方文档：https://modelcontextprotocol.io/
- MCP SDK 列表：https://modelcontextprotocol.io/docs/sdk
- MCP Transports 规范：https://modelcontextprotocol.io/specification/2025-03-26/basic/transports
- MCP 2025-03-26 Changelog：https://modelcontextprotocol.io/specification/2025-03-26/changelog
- TypeScript SDK：https://github.com/modelcontextprotocol/typescript-sdk
- Python SDK：https://github.com/modelcontextprotocol/python-sdk
- Nacos 文档：https://nacos.io/
