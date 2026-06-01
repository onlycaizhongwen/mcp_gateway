# Java MCP Server Nacos 注册 helper 示例

该目录提供 Java 业务 MCP Server 可复制的 Nacos 注册 starter，使用 JDK 8 标准库实现，不引入额外依赖。

能力包括：

- 注册 MCP Server 实例到 Nacos。
- 写入 `metadata.mcp` JSON 字符串，兼容 Gateway 当前 discovery parser。
- 注销 MCP Server 实例。
- 发送 Nacos ephemeral 实例心跳。
- 使用 `AutoCloseable` 生命周期封装启动注册、关闭注销和心跳线程收口。

## 文件说明

- `NacosMcpServerRegistrar.java`：Nacos OpenAPI 注册、注销、心跳和鉴权 token 获取。
- `McpServerNacosLifecycle.java`：业务服务生命周期封装。
- `KnowledgeSearchMetadata.java`：`knowledge.search` 示例 metadata。
- `RegisterMcpServerExample.java`：注册、心跳和 shutdown hook 示例。

## 编译示例

```bash
javac -d build/classes *.java
```

## 使用建议

真实业务服务接入时，将 `McpServerNacosLifecycle.start()` 放到服务启动成功后的生命周期钩子中，将 `close()` 放到 shutdown hook 或容器销毁回调中。

如果服务已经使用 Spring Cloud Alibaba Nacos、Dubbo 或公司统一注册 SDK，优先复用现有 SDK 管理实例生命周期；本 helper 可作为 metadata 格式和 MCP 工具注册字段参考。
