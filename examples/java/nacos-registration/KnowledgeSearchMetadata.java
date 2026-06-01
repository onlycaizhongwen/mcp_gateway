package com.example.mcp.nacos;

public final class KnowledgeSearchMetadata {
    private KnowledgeSearchMetadata() {
    }

    public static String json() {
        return "{"
                + "\"metadataVersion\":\"1.0\","
                + "\"mcpProtocolVersion\":\"2025-03-26\","
                + "\"transport\":\"streamable-http\","
                + "\"endpoint\":\"/mcp\","
                + "\"healthPath\":\"/health\","
                + "\"domain\":\"knowledge\","
                + "\"serverVersion\":\"1.0.0\","
                + "\"toolSetVersion\":\"1.0.0\","
                + "\"tenantMode\":\"shared\","
                + "\"authType\":\"gateway-token\","
                + "\"enabled\":true,"
                + "\"labels\":[\"example\",\"knowledge\"],"
                + "\"tools\":[{"
                + "\"name\":\"knowledge.search\","
                + "\"version\":\"1.0.0\","
                + "\"description\":\"Search enterprise knowledge base\","
                + "\"inputSchemaRef\":\"nacos://mcp-schemas/knowledge.search/1.0.0/input\","
                + "\"outputSchemaRef\":\"nacos://mcp-schemas/knowledge.search/1.0.0/output\","
                + "\"readOnly\":true,"
                + "\"destructive\":false,"
                + "\"idempotent\":true,"
                + "\"enabled\":true"
                + "}]"
                + "}";
    }
}
