package com.example.mcp.nacos;

import com.example.mcp.nacos.NacosMcpServerRegistrar.McpServerRegistration;
import com.example.mcp.nacos.NacosMcpServerRegistrar.NacosRegistrationConfig;

import java.time.Duration;

public final class RegisterMcpServerExample {
    private RegisterMcpServerExample() {
    }

    public static void main(String[] args) throws Exception {
        NacosMcpServerRegistrar registrar = new NacosMcpServerRegistrar(
                new NacosRegistrationConfig(
                        "http://127.0.0.1:8848",
                        "dev",
                        "MCP_SERVER_GROUP",
                        null,
                        null,
                        Duration.ofSeconds(3)));
        McpServerRegistration registration = new McpServerRegistration(
                "mcp-server-knowledge",
                "127.0.0.1",
                18081,
                KnowledgeSearchMetadata.json(),
                100,
                true,
                true,
                true);

        try (McpServerNacosLifecycle lifecycle = new McpServerNacosLifecycle(
                registrar,
                registration,
                true,
                Duration.ofSeconds(5))) {
            lifecycle.start();
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                try {
                    lifecycle.close();
                } catch (Exception ignored) {
                    // Shutdown hook must not block process exit.
                }
            }));

            // Start the actual MCP Server here and block until it exits.
            Thread.currentThread().join();
        }
    }
}
