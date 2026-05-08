KNOWLEDGE_INSTANCE = {
    "service_name": "mcp-server-knowledge",
    "instance_id": "knowledge-1",
    "host": "127.0.0.1",
    "port": 18081,
    "weight": 100,
    "healthy": True,
    "metadata": {
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
        "enabled": True,
        "labels": ["local", "mock"],
        "tools": [
            {
                "name": "knowledge.search",
                "version": "1.0.0",
                "description": "Search enterprise knowledge base",
                "inputSchemaRef": "nacos://mcp-schemas/knowledge.search/1.0.0/input",
                "outputSchemaRef": "nacos://mcp-schemas/knowledge.search/1.0.0/output",
                "readOnly": True,
                "destructive": False,
                "idempotent": True,
                "enabled": True,
            }
        ],
    },
}

APPROVAL_INSTANCE = {
    "service_name": "mcp-server-approval",
    "instance_id": "approval-1",
    "host": "127.0.0.1",
    "port": 18082,
    "weight": 100,
    "healthy": True,
    "metadata": {
        "metadataVersion": "1.0",
        "mcpProtocolVersion": "2025-03-26",
        "transport": "streamable-http",
        "endpoint": "/mcp",
        "healthPath": "/health",
        "domain": "approval",
        "serverVersion": "1.0.0",
        "toolSetVersion": "1.0.0",
        "tenantMode": "shared",
        "authType": "gateway-token",
        "enabled": True,
        "labels": ["local", "mock"],
        "tools": [
            {
                "name": "approval.create_task",
                "version": "1.0.0",
                "description": "Create an approval task",
                "inputSchemaRef": "nacos://mcp-schemas/approval.create_task/1.0.0/input",
                "outputSchemaRef": "nacos://mcp-schemas/approval.create_task/1.0.0/output",
                "readOnly": False,
                "destructive": False,
                "idempotent": False,
                "enabled": True,
            }
        ],
    },
}

DOCUMENT_INSTANCE = {
    "service_name": "mcp-server-document",
    "instance_id": "document-1",
    "host": "127.0.0.1",
    "port": 18083,
    "weight": 100,
    "healthy": True,
    "metadata": {
        "metadataVersion": "1.0",
        "mcpProtocolVersion": "2025-03-26",
        "transport": "streamable-http",
        "endpoint": "/mcp",
        "healthPath": "/health",
        "domain": "document",
        "serverVersion": "1.0.0",
        "toolSetVersion": "1.0.0",
        "tenantMode": "shared",
        "authType": "gateway-token",
        "enabled": True,
        "labels": ["local", "mock"],
        "tools": [
            {
                "name": "document.generate",
                "version": "1.0.0",
                "description": "Generate a business document draft",
                "inputSchemaRef": "nacos://mcp-schemas/document.generate/1.0.0/input",
                "outputSchemaRef": "nacos://mcp-schemas/document.generate/1.0.0/output",
                "readOnly": False,
                "destructive": False,
                "idempotent": False,
                "enabled": True,
            }
        ],
    },
}

SAMPLE_NACOS_INSTANCES = [
    KNOWLEDGE_INSTANCE,
    APPROVAL_INSTANCE,
    DOCUMENT_INSTANCE,
]
