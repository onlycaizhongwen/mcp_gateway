# Schema Registry Nacos Config Backend

## 恢复胶囊

- 任务需求：替换内存 schema registry 为 Nacos Config 或独立元数据服务。
- 关键决策：先实现可配置后端，默认 `memory` 保持本地兼容；新增 `nacos_config` 后端作为测试环境可用方案，独立元数据服务保留为后续演进项。
- 当前阶段：已完成并通过本地 Docker Nacos mock 数据联调验证。
- 已完成产物：`SchemaRegistryConfig`、`NacosConfigSchemaRegistry`、`create_schema_registry()`、配置样例、单元测试和文档同步。
- 剩余工作：无属于本任务的剩余工作；公司测试/生产 Nacos 参数、网络策略和生产变更流程仍需在后续环境任务中处理。

## 步骤列表

- [v] 核对现有 schema ref 约定。
- [v] 新增 `schema_registry.mode=memory|nacos_config` 配置。
- [v] 新增 Nacos Config 拉取逻辑和 schema 缓存。
- [v] 复用 Nacos endpoint、namespace、username、password、timeout 默认值。
- [v] 补充 config/schema registry 单元测试。
- [v] 更新 README、交付说明、status 和 trace。
- [v] 新增 Nacos Config schema 发布脚本。
- [v] 在本地 Docker Nacos 发布 mock schema，并验证 `/schema`、缺参校验和工具调用链路。

## 研究发现

- 当前 schema ref 格式为 `nacos://mcp-schemas/{tool}/{version}/{input|output}`。
- Nacos Config 后端映射为 `dataId=mcp-schemas__{tool}__{version}__{input|output}.json`，默认 `group=MCP_SCHEMA_GROUP`，避免真实 Nacos Config 拒绝 `/` 字符。
- Nacos Config namespace 参数使用 OpenAPI `tenant`。

## 错误记录

- 暂无。
