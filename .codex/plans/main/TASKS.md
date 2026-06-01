# TASKS

## v1-mcp-gateway-nacos-discovery-技术设计
- 状态：已完成
- 摘要：基于企业 AI 升级项目工具层需求，规划 MCP Server 自动注册到 Nacos、MCP 网关动态发现与调度的设计方案。
- 过程文件：.codex/plans/main/mcp-gateway-nacos-discovery-design/process.md
- 恢复提示：如需继续推进，读取 design 文档后进入执行计划或实现阶段。

## mcp-sdk-adapter-replacement
- 状态：已完成
- 摘要：将网关 Streamable HTTP client 从手写 JSON-RPC 调用替换为官方 Python MCP SDK adapter。
- 过程文件：.codex/plans/main/mcp-sdk-adapter/process.md
- 恢复提示：如需继续生产化，优先处理 schema registry、外部 Nacos 环境联调、真实业务系统接入和指标告警。

## schema-registry-nacos-config
- 状态：已完成
- 摘要：将 schema registry 从纯内存样例升级为可配置后端，支持 Nacos Config 读取工具 schema。
- 过程文件：.codex/plans/main/schema-registry-nacos-config/process.md
- 恢复提示：如需继续生产化，下一步优先做外部 Nacos 测试环境联调或指标/审计落地。

## production-observability
- 状态：已完成
- 摘要：新增 Prometheus 文本格式 `/metrics` 基础指标出口，覆盖工具调用结果、耗时汇总和 Catalog 刷新快照。
- 过程文件：.codex/plans/main/production-observability/process.md
- 恢复提示：后续如继续生产化，优先接公司指标平台采集、告警规则和审计落库。

## mcp-server-registration-lifecycle
- 状态：已完成
- 摘要：新增 Python MCP Server 注册生命周期封装，支持启动注册到 Nacos、关闭或异常退出时注销。
- 过程文件：.codex/plans/main/mcp-server-registration-lifecycle/process.md
- 恢复提示：后续如继续生产化，优先将该 helper 嵌入真实业务 MCP Server 或补充 Java/其他语言版本。

## java-mcp-server-registration-helper
- 状态：已完成
- 摘要：新增 Java MCP Server Nacos 注册 helper 示例，覆盖注册、注销、ephemeral 心跳和生命周期封装。
- 过程文件：.codex/plans/main/java-mcp-server-registration-helper/process.md
- 恢复提示：后续如继续生产化，将 Java helper 嵌入真实业务 MCP Server，或改造为公司内部 starter。
