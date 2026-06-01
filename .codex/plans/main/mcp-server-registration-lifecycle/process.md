# MCP Server 注册生命周期封装

## 1. 恢复胶囊

- 任务需求：继续推进生产化待办中“真实 MCP Server 注册”和“生产心跳策略”方向，先补本地可验证的注册生命周期封装和 Nacos ephemeral 心跳能力。
- 关键决策：不强行改示例 MCP Server 启动方式，避免本地演示启动依赖 Nacos；在现有 Python 注册 helper 上提供可复用生命周期对象，并仅在 `ephemeral=True` 且配置心跳间隔时启动心跳线程。
- 当前阶段：已完成。
- 已完成产物：`McpServerNacosLifecycle`、`send_heartbeat()`、注册生命周期和 Nacos beat 单元测试、README、Nacos 联调说明、交付说明和状态文档更新。
- 剩余工作：真实业务 MCP Server 需要在自身启动/关闭钩子中嵌入；非 Python 服务需补对应语言版本或复用自身 Nacos SDK。
- 重要发现：现有 `NacosMcpServerRegistrar` 已具备注册、注销和鉴权 token 获取能力，缺口主要是调用方需要手写 try/finally。

## 2. 步骤列表

- [v] 阅读现有 Nacos 注册 helper、命令行示例和测试。
- [v] 新增生命周期封装，支持幂等 start/stop 和 context manager。
- [v] 补充启动注册、退出注销、异常退出注销测试。
- [v] 同步 README、联调说明、交付说明和状态文档。
- [v] 新增 Nacos beat 心跳请求封装。
- [v] 生命周期支持 ephemeral 实例启动心跳线程，停止时收口线程。
- [v] 补充心跳请求和 ephemeral 生命周期测试。
- [~] 下一步：如继续推进真实 MCP Server 接入，将 helper 嵌入业务服务生命周期，或补 Java 版注册 helper。

## 3. 验证记录

- `python -m pytest tests/test_nacos_registration.py`：7 passed。
- `python -m pytest`：79 passed。
