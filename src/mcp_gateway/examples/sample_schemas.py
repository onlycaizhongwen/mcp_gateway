SAMPLE_SCHEMAS = {
    "nacos://mcp-schemas/knowledge.search/1.0.0/input": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "自然语言查询问题",
                "maxLength": 1000,
            },
            "top_k": {
                "type": "integer",
                "description": "返回结果数量",
                "default": 3,
                "minimum": 1,
                "maximum": 10,
            },
            "threshold": {
                "type": "number",
                "description": "相似度阈值",
                "default": 0.7,
                "minimum": 0,
                "maximum": 1,
            },
            "scope": {
                "type": "array",
                "items": {"type": "string"},
                "description": "知识范围",
            },
        },
        "required": ["query"],
    },
    "nacos://mcp-schemas/knowledge.search/1.0.0/output": {
        "type": "object",
        "properties": {
            "answer": {"type": "string"},
            "references": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "source": {"type": "string"},
                        "score": {"type": "number"},
                    },
                },
            },
        },
        "required": ["answer"],
    },
    "nacos://mcp-schemas/approval.create_task/1.0.0/input": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "审批标题"},
            "applicant": {"type": "string", "description": "申请人"},
            "approver": {"type": "string", "description": "审批人"},
            "payload": {"type": "object", "description": "审批业务数据"},
        },
        "required": ["title", "applicant", "approver"],
    },
    "nacos://mcp-schemas/approval.create_task/1.0.0/output": {
        "type": "object",
        "properties": {
            "taskId": {"type": "string"},
            "status": {"type": "string"},
            "approvalUrl": {"type": "string"},
        },
        "required": ["taskId", "status"],
    },
    "nacos://mcp-schemas/document.generate/1.0.0/input": {
        "type": "object",
        "properties": {
            "template": {"type": "string", "description": "文档模板编码"},
            "title": {"type": "string", "description": "文档标题"},
            "variables": {"type": "object", "description": "模板变量"},
            "format": {"type": "string", "description": "输出格式", "default": "markdown"},
        },
        "required": ["template", "title"],
    },
    "nacos://mcp-schemas/document.generate/1.0.0/output": {
        "type": "object",
        "properties": {
            "documentId": {"type": "string"},
            "title": {"type": "string"},
            "format": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["documentId", "content"],
    },
}
