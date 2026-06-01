package com.example.mcp.nacos;

import java.io.IOException;
import java.net.URLEncoder;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.StringJoiner;

public final class NacosMcpServerRegistrar {
    private final NacosRegistrationConfig config;
    private String accessToken;

    public NacosMcpServerRegistrar(NacosRegistrationConfig config) {
        this.config = Objects.requireNonNull(config, "config");
    }

    public String registerInstance(McpServerRegistration registration)
            throws IOException, InterruptedException {
        return sendForm("POST", "/nacos/v1/ns/instance", buildRegisterPayload(registration));
    }

    public String deregisterInstance(String serviceName, String ip, int port)
            throws IOException, InterruptedException {
        Map<String, String> payload = baseInstancePayload(serviceName, ip, port);
        return sendForm("DELETE", "/nacos/v1/ns/instance", payload);
    }

    public String sendHeartbeat(McpServerRegistration registration)
            throws IOException, InterruptedException {
        Map<String, String> payload = baseInstancePayload(
                registration.serviceName(),
                registration.ip(),
                registration.port());
        payload.put("ephemeral", Boolean.toString(registration.ephemeral()));
        payload.put("beat", buildBeatPayload(registration));
        return sendForm("PUT", "/nacos/v1/ns/instance/beat", payload);
    }

    private Map<String, String> buildRegisterPayload(McpServerRegistration registration) {
        Map<String, String> payload = baseInstancePayload(
                registration.serviceName(),
                registration.ip(),
                registration.port());
        payload.put("weight", Integer.toString(registration.weight()));
        payload.put("enabled", Boolean.toString(registration.enabled()));
        payload.put("healthy", Boolean.toString(registration.healthy()));
        payload.put("ephemeral", Boolean.toString(registration.ephemeral()));
        payload.put("metadata", "{\"mcp\":" + quote(registration.mcpMetadataJson()) + "}");
        return payload;
    }

    private Map<String, String> baseInstancePayload(String serviceName, String ip, int port) {
        Map<String, String> payload = new LinkedHashMap<>();
        payload.put("serviceName", serviceName);
        payload.put("groupName", config.group());
        payload.put("ip", ip);
        payload.put("port", Integer.toString(port));
        if (config.namespace() != null && !config.namespace().trim().isEmpty()) {
            payload.put("namespaceId", config.namespace());
        }
        return payload;
    }

    private String buildBeatPayload(McpServerRegistration registration) {
        return "{"
                + "\"serviceName\":" + quote(registration.serviceName()) + ","
                + "\"ip\":" + quote(registration.ip()) + ","
                + "\"port\":" + registration.port() + ","
                + "\"weight\":" + registration.weight() + ","
                + "\"ephemeral\":" + registration.ephemeral() + ","
                + "\"scheduled\":true,"
                + "\"metadata\":{\"mcp\":" + quote(registration.mcpMetadataJson()) + "}"
                + "}";
    }

    private String sendForm(String method, String path, Map<String, String> payload)
            throws IOException, InterruptedException {
        Map<String, String> body = new LinkedHashMap<>(payload);
        String token = accessToken();
        if (token != null && !token.trim().isEmpty()) {
            body.put("accessToken", token);
        }
        return sendHttpForm(method, trimTrailingSlash(config.endpoint()) + path, body);
    }

    private String accessToken() throws IOException, InterruptedException {
        if (config.username() == null || config.password() == null) {
            return null;
        }
        if (accessToken != null) {
            return accessToken;
        }
        Map<String, String> payload = new LinkedHashMap<>();
        payload.put("username", config.username());
        payload.put("password", config.password());
        String body = sendHttpForm(
                "POST",
                trimTrailingSlash(config.endpoint()) + "/nacos/v1/auth/login",
                payload);
        accessToken = extractJsonString(body, "accessToken");
        return accessToken;
    }

    private String sendHttpForm(String method, String url, Map<String, String> payload)
            throws IOException {
        byte[] body = formEncode(payload).getBytes(StandardCharsets.UTF_8);
        HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
        connection.setConnectTimeout((int) config.timeout().toMillis());
        connection.setReadTimeout((int) config.timeout().toMillis());
        connection.setRequestMethod(method);
        connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
        connection.setDoOutput(true);
        try (OutputStream outputStream = connection.getOutputStream()) {
            outputStream.write(body);
        }
        int status = connection.getResponseCode();
        byte[] responseBytes;
        if (status >= 400) {
            responseBytes = connection.getErrorStream() == null
                    ? new byte[0]
                    : readAllBytes(connection.getErrorStream());
            throw new IOException("Nacos request failed: status="
                    + status
                    + ", body="
                    + new String(responseBytes, StandardCharsets.UTF_8));
        }
        responseBytes = readAllBytes(connection.getInputStream());
        return new String(responseBytes, StandardCharsets.UTF_8);
    }

    private static byte[] readAllBytes(java.io.InputStream inputStream) throws IOException {
        java.io.ByteArrayOutputStream buffer = new java.io.ByteArrayOutputStream();
        byte[] data = new byte[4096];
        int length;
        while ((length = inputStream.read(data)) != -1) {
            buffer.write(data, 0, length);
        }
        return buffer.toByteArray();
    }

    private static String formEncode(Map<String, String> payload) {
        StringJoiner joiner = new StringJoiner("&");
        for (Map.Entry<String, String> entry : payload.entrySet()) {
            joiner.add(urlEncode(entry.getKey()) + "=" + urlEncode(entry.getValue()));
        }
        return joiner.toString();
    }

    private static String urlEncode(String value) {
        try {
            return URLEncoder.encode(value, StandardCharsets.UTF_8.name());
        } catch (java.io.UnsupportedEncodingException ex) {
            throw new IllegalStateException("UTF-8 is not supported", ex);
        }
    }

    private static String trimTrailingSlash(String endpoint) {
        if (endpoint.endsWith("/")) {
            return endpoint.substring(0, endpoint.length() - 1);
        }
        return endpoint;
    }

    private static String quote(String value) {
        StringBuilder builder = new StringBuilder(value.length() + 2);
        builder.append('"');
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            switch (c) {
                case '"':
                    builder.append("\\\"");
                    break;
                case '\\':
                    builder.append("\\\\");
                    break;
                case '\b':
                    builder.append("\\b");
                    break;
                case '\f':
                    builder.append("\\f");
                    break;
                case '\n':
                    builder.append("\\n");
                    break;
                case '\r':
                    builder.append("\\r");
                    break;
                case '\t':
                    builder.append("\\t");
                    break;
                default:
                    if (c < 0x20) {
                        builder.append(String.format("\\u%04x", (int) c));
                    } else {
                        builder.append(c);
                    }
            }
        }
        builder.append('"');
        return builder.toString();
    }

    private static String extractJsonString(String json, String fieldName) throws IOException {
        String marker = quote(fieldName) + ":";
        int markerIndex = json.indexOf(marker);
        if (markerIndex < 0) {
            throw new IOException("Missing JSON field: " + fieldName);
        }
        int start = json.indexOf('"', markerIndex + marker.length());
        if (start < 0) {
            throw new IOException("Invalid JSON field: " + fieldName);
        }
        StringBuilder value = new StringBuilder();
        boolean escaping = false;
        for (int i = start + 1; i < json.length(); i++) {
            char c = json.charAt(i);
            if (escaping) {
                value.append(c);
                escaping = false;
                continue;
            }
            if (c == '\\') {
                escaping = true;
                continue;
            }
            if (c == '"') {
                return value.toString();
            }
            value.append(c);
        }
        throw new IOException("Unterminated JSON field: " + fieldName);
    }

    public static final class NacosRegistrationConfig {
        private final String endpoint;
        private final String namespace;
        private final String group;
        private final String username;
        private final String password;
        private final Duration timeout;

        public NacosRegistrationConfig(
                String endpoint,
                String namespace,
                String group,
                String username,
                String password,
                Duration timeout) {
            this.endpoint = endpoint == null || endpoint.trim().isEmpty()
                    ? "http://127.0.0.1:8848"
                    : endpoint;
            this.namespace = namespace;
            this.group = group == null || group.trim().isEmpty() ? "MCP_SERVER_GROUP" : group;
            this.username = username;
            this.password = password;
            this.timeout = timeout == null ? Duration.ofSeconds(3) : timeout;
        }

        public String endpoint() {
            return endpoint;
        }

        public String namespace() {
            return namespace;
        }

        public String group() {
            return group;
        }

        public String username() {
            return username;
        }

        public String password() {
            return password;
        }

        public Duration timeout() {
            return timeout;
        }
    }

    public static final class McpServerRegistration {
        private final String serviceName;
        private final String ip;
        private final int port;
        private final String mcpMetadataJson;
        private final int weight;
        private final boolean enabled;
        private final boolean healthy;
        private final boolean ephemeral;

        public McpServerRegistration(
                String serviceName,
                String ip,
                int port,
                String mcpMetadataJson,
                int weight,
                boolean enabled,
                boolean healthy,
                boolean ephemeral) {
            this.serviceName = Objects.requireNonNull(serviceName, "serviceName");
            this.ip = Objects.requireNonNull(ip, "ip");
            this.port = port;
            this.mcpMetadataJson = Objects.requireNonNull(mcpMetadataJson, "mcpMetadataJson");
            this.weight = weight;
            this.enabled = enabled;
            this.healthy = healthy;
            this.ephemeral = ephemeral;
        }

        public String serviceName() {
            return serviceName;
        }

        public String ip() {
            return ip;
        }

        public int port() {
            return port;
        }

        public String mcpMetadataJson() {
            return mcpMetadataJson;
        }

        public int weight() {
            return weight;
        }

        public boolean enabled() {
            return enabled;
        }

        public boolean healthy() {
            return healthy;
        }

        public boolean ephemeral() {
            return ephemeral;
        }
    }
}
