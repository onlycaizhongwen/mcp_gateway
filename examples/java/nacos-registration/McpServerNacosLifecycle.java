package com.example.mcp.nacos;

import com.example.mcp.nacos.NacosMcpServerRegistrar.McpServerRegistration;

import java.time.Duration;
import java.util.Objects;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public final class McpServerNacosLifecycle implements AutoCloseable {
    private final NacosMcpServerRegistrar registrar;
    private final McpServerRegistration registration;
    private final boolean deregisterOnClose;
    private final Duration heartbeatInterval;
    private ScheduledExecutorService heartbeatExecutor;
    private boolean registered;

    public McpServerNacosLifecycle(
            NacosMcpServerRegistrar registrar,
            McpServerRegistration registration,
            boolean deregisterOnClose,
            Duration heartbeatInterval) {
        this.registrar = Objects.requireNonNull(registrar, "registrar");
        this.registration = Objects.requireNonNull(registration, "registration");
        this.deregisterOnClose = deregisterOnClose;
        this.heartbeatInterval = heartbeatInterval;
    }

    public synchronized void start() throws Exception {
        if (registered) {
            return;
        }
        registrar.registerInstance(registration);
        registered = true;
        try {
            startHeartbeatIfNeeded();
        } catch (Exception ex) {
            close();
            throw ex;
        }
    }

    public synchronized boolean registered() {
        return registered;
    }

    @Override
    public synchronized void close() throws Exception {
        stopHeartbeat();
        if (!registered || !deregisterOnClose) {
            return;
        }
        registrar.deregisterInstance(
                registration.serviceName(),
                registration.ip(),
                registration.port());
        registered = false;
    }

    private void startHeartbeatIfNeeded() throws Exception {
        if (!registration.ephemeral() || heartbeatInterval == null) {
            return;
        }
        registrar.sendHeartbeat(registration);
        heartbeatExecutor = Executors.newSingleThreadScheduledExecutor(runnable -> {
            Thread thread = new Thread(runnable, "nacos-heartbeat-" + registration.serviceName());
            thread.setDaemon(true);
            return thread;
        });
        heartbeatExecutor.scheduleAtFixedRate(
                () -> {
                    try {
                        registrar.sendHeartbeat(registration);
                    } catch (Exception ignored) {
                        // Keep the heartbeat loop alive; surface failures via service logs in real apps.
                    }
                },
                heartbeatInterval.toMillis(),
                heartbeatInterval.toMillis(),
                TimeUnit.MILLISECONDS);
    }

    private void stopHeartbeat() {
        if (heartbeatExecutor == null) {
            return;
        }
        heartbeatExecutor.shutdownNow();
        heartbeatExecutor = null;
    }
}
