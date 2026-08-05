package com.enterprise.ai.gateway.proxy;

import com.enterprise.ai.gateway.audit.AuditLogService;
import com.enterprise.ai.gateway.auth.JwtTokenProvider;
import com.enterprise.ai.gateway.tenant.TenantContext;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;

import org.springframework.web.bind.annotation.*;

import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Controller proxying streaming chat SSE requests from clients to the backend Python Orchestration service.
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/chat")
@RequiredArgsConstructor
public class OrchestratorProxyController {

    @Value("${gateway.orchestrator.url:http://localhost:8000}")
    private String orchestratorUrl;

    private final JwtTokenProvider tokenProvider;
    private final AuditLogService auditLogService;
    private final ExecutorService executor = Executors.newCachedThreadPool();

    /**
     * Proxies streaming chat completion SSE connection from gateway to Python orchestrator backend.
     * 
     * @param requestBody Chat request parameters map.
     * @return SseEmitter instance for streaming response events.
     */
    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamChat(@RequestBody Map<String, Object> requestBody) {
        String tenantId = TenantContext.getTenantId();
        String userId = TenantContext.getUserId();
        String role = TenantContext.getUserRole();

        String conversationId = (String) requestBody.get("conversation_id");
        log.info("Initiating streaming chat proxy for conversation [{}] (tenant: {}, user: {})", conversationId, tenantId, userId);

        // Audit Log entry
        try {
            auditLogService.logEvent(
                    UUID.fromString(tenantId),
                    UUID.fromString(userId),
                    "CHAT_STREAM_INITIATED",
                    "CONVERSATION",
                    conversationId,
                    null,
                    requestBody.toString()
            );
        } catch (Exception auditErr) {
            log.error("Failed to write audit log entry for chat stream: {}", auditErr.getMessage(), auditErr);
        }

        String serviceToken = tokenProvider.generateInternalServiceToken(tenantId, userId, role);
        SseEmitter emitter = new SseEmitter(180000L); // 3 minutes timeout

        emitter.onTimeout(() -> log.warn("SSE emitter timed out for conversation [{}]", conversationId));
        emitter.onError(ex -> log.error("SSE emitter error for conversation [{}]: {}", conversationId, ex.getMessage()));
        emitter.onCompletion(() -> log.debug("SSE emitter completed for conversation [{}]", conversationId));

        executor.execute(() -> {
            try {
                HttpClient client = HttpClient.newHttpClient();
                String requestJson = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(requestBody);

                HttpRequest httpRequest = HttpRequest.newBuilder()
                        .uri(URI.create(orchestratorUrl + "/api/v1/stream"))
                        .header(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                        .header("X-Service-Token", serviceToken)
                        .header("X-Tenant-Id", tenantId)
                        .header("X-User-Id", userId)
                        .POST(HttpRequest.BodyPublishers.ofString(requestJson))
                        .build();

                log.debug("Sending SSE HTTP POST to upstream orchestrator: {}", httpRequest.uri());
                HttpResponse<InputStream> httpResponse = client.send(httpRequest, HttpResponse.BodyHandlers.ofInputStream());

                if (httpResponse.statusCode() >= 400) {
                    log.error("Upstream orchestrator returned non-success status code [{}] for conversation [{}]", 
                            httpResponse.statusCode(), conversationId);
                    emitter.send(SseEmitter.event().name("error").data("Upstream orchestrator error: " + httpResponse.statusCode()));
                    emitter.complete();
                    return;
                }

                try (InputStream inputStream = httpResponse.body()) {
                    byte[] buffer = new byte[1024];
                    int bytesRead;
                    StringBuilder lineBuffer = new StringBuilder();

                    while ((bytesRead = inputStream.read(buffer)) != -1) {
                        String chunk = new String(buffer, 0, bytesRead, StandardCharsets.UTF_8);
                        lineBuffer.append(chunk);

                        int newlineIndex;
                        while ((newlineIndex = lineBuffer.indexOf("\n")) != -1) {
                            String line = lineBuffer.substring(0, newlineIndex).trim();
                            lineBuffer.delete(0, newlineIndex + 1);

                            if (!line.isEmpty()) {
                                emitter.send(SseEmitter.event().data(line));
                            }
                        }
                    }
                }
                log.info("Successfully completed streaming response from orchestrator for conversation [{}]", conversationId);
                emitter.complete();
            } catch (Exception e) {
                log.error("Error encountered while streaming from orchestrator backend for conversation [{}]: {}", 
                        conversationId, e.getMessage(), e);
                emitter.completeWithError(e);
            }
        });

        return emitter;
    }
}

