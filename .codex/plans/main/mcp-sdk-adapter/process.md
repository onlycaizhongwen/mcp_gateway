# MCP SDK Adapter Replacement

## 恢复胶囊

- 任务需求：替换最小 Streamable HTTP client 为官方 Python MCP SDK adapter。
- 关键决策：锁定 `mcp==1.27.1`；保留网关现有同步 `McpClient.call_tool()` 协议，在内部用 `anyio.run()` 调用 SDK 异步 Streamable HTTP client。
- 当前阶段：已完成并验证。
- 已完成产物：`src/mcp_gateway/client/streamable_http_client.py`、`tests/test_streamable_http_client.py`、`examples/mock_mcp_server.py`、`pyproject.toml` 和相关 README/docs 更新。
- 剩余工作：无属于本任务的剩余工作；项目级剩余项仍包括 schema registry 持久化、外部 Nacos 测试环境联调、真实业务系统接入、生产指标/审计/告警。
- 重要发现：官方 SDK 调用链需要先 `ClientSession.initialize()`，因此本地示例 MCP Server 也改为 FastMCP，避免旧手写 JSON-RPC mock 无法响应初始化。

## 步骤列表

- [v] 核对官方 SDK 包和 Streamable HTTP API。
- [v] 替换手写 JSON-RPC client 为官方 SDK adapter。
- [v] 更新本地示例 MCP Server 为 FastMCP。
- [v] 补充单元测试，覆盖 SDK session 初始化、调用和错误映射。
- [v] 更新 README、交付、status、trace、Nacos 联调说明。
- [v] 运行 `python -m pytest`，结果 `56 passed`。
- [v] 启动本地 FastMCP 示例服务并通过 Gateway SDK adapter 完成端到端烟测。

## 研究发现

- `mcp==1.27.1` 提供 `mcp.client.streamable_http.streamable_http_client` 和 `mcp.ClientSession`。
- SDK 返回 `CallToolResult`；网关优先取 `structuredContent` 作为现有 API 的 dict 返回。
- `CallToolResult.isError=True` 时，网关映射为 `MCP_TOOL_EXECUTION_FAILED`/502。

## 错误记录

- 首次补丁因测试文件中的历史中文编码显示与 patch 上下文不一致未套上；已改为整文件替换相关 client/test 文件解决。
