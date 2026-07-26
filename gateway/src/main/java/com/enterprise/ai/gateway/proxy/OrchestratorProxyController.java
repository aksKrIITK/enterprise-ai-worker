package com.enterprise.ai.gateway.proxy;

import com.enterprise.ai.gateway.audit.AuditLogService;
import com.enterprise.ai.gateway.auth.JwtTokenProvider;
import com.enterprise.ai.gateway.tenant.TenantContext;
import lombok.RequiredArgsConstructor;
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

@RestController
@RequestMapping("/api/v1/chat")
@RequiredArgsConstructor
public class OrchestratorProxyController {

    @Value("${gateway.orchestrator.url:http://localhost:8000}")
    private String orchestratorUrl;

    private final JwtTokenProvider tokenProvider;
    private final AuditLogService auditLogService;
    private final ExecutorService executor = Executors.newCachedThreadPool();

    @PostMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamChat(@RequestBody Map<String, Object> requestBody) {
        String tenantId = TenantContext.getTenantId();
        String userId = TenantContext.getUserId();
        String role = TenantContext.getUserRole();

        // Audit Log entry
        auditLogService.logEvent(
                UUID.fromString(tenantId),
                UUID.fromString(userId),
                "CHAT_STREAM_INITIATED",
                "CONVERSATION",
                (String) requestBody.get("conversation_id"),
                null,
                requestBody.toString()
        );

        String serviceToken = tokenProvider.generateInternalServiceToken(tenantId, userId, role);
        SseEmitter emitter = new SseEmitter(180000L); // 3 minutes timeout

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

                HttpResponse<InputStream> httpResponse = client.send(httpRequest, HttpResponse.BodyHandlers.ofInputStream());

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
                emitter.complete();
            } catch (Exception e) {
                emitter.completeWithError(e);
            }
        });

        return emitter;
    }
}
