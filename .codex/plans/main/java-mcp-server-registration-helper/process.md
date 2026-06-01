# Java MCP Server Nacos 注册 Helper

## 1. 恢复胶囊

- 任务需求：继续生产化真实 MCP Server 注册接入，补 Java 版注册 helper 示例。
- 关键决策：示例使用 JDK 标准库 `java.net.http.HttpClient`，不引入 Maven/Gradle 依赖；将其定位为业务 Java MCP Server 可复制 starter。
- 当前阶段：已完成。
- 已完成产物：`examples/java/nacos-registration/`、Java helper 契约测试、README、Nacos 联调说明、交付说明、trace 和 status 更新。
- 剩余工作：真实业务 Java MCP Server 需要按自身框架生命周期嵌入；如果公司已有 Nacos SDK/starter，应优先复用并迁移 metadata 约定。
- 重要发现：当前仓库没有 Java 构建系统，因此用 pytest 校验源码契约；如本机有 `javac`，测试会实际编译示例。

## 2. 步骤列表

- [v] 新增 Java registrar，覆盖 Nacos 注册、注销、心跳和鉴权 token 获取。
- [v] 新增 Java lifecycle，使用 `AutoCloseable` 管理启动注册、关闭注销和心跳线程。
- [v] 新增 `knowledge.search` metadata 示例和 main 示例。
- [v] 新增 Java 示例 README。
- [v] 补充测试校验 Java 示例契约和可编译性。
- [~] 下一步：将 Java helper 嵌入真实业务 MCP Server，或整理为公司内部 starter。

## 3. 验证记录

- `python -m pytest tests/test_java_nacos_registration_example.py`：2 passed，包含本机 JDK 8 编译验证。
- `python -m pytest`：81 passed。
