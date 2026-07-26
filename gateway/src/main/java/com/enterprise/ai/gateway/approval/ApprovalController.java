package com.enterprise.ai.gateway.approval;

import com.enterprise.ai.gateway.audit.AuditLogService;
import com.enterprise.ai.gateway.auth.JwtTokenProvider;
import com.enterprise.ai.gateway.tenant.TenantContext;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/approvals")
public class ApprovalController {

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private ApprovalRequestRepository approvalRequestRepository;

    private final AuditLogService auditLogService;
    private final JwtTokenProvider tokenProvider;
    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${gateway.orchestrator.url:http://localhost:8000}")
    private String orchestratorUrl;

    public ApprovalController(AuditLogService auditLogService, JwtTokenProvider tokenProvider) {
        this.auditLogService = auditLogService;
        this.tokenProvider = tokenProvider;
    }

    @GetMapping("/pending")
    public ResponseEntity<List<ApprovalRequest>> getPendingApprovals() {
        String tenantId = TenantContext.getTenantId();
        if (approvalRequestRepository == null) {
            return ResponseEntity.ok(List.of());
        }
        List<ApprovalRequest> pending = approvalRequestRepository
                .findByTenantIdAndStatusOrderByCreatedAtDesc(UUID.fromString(tenantId), "pending");
        return ResponseEntity.ok(pending);
    }


    @PostMapping("/{id}/approve")
    @PreAuthorize("hasAnyRole('OWNER', 'ADMIN')")
    public ResponseEntity<Map<String, Object>> approveAction(
            @PathVariable("id") String requestId,
            @RequestBody(required = false) Map<String, Object> body) {

        String tenantId = TenantContext.getTenantId();
        String userId = TenantContext.getUserId();

        auditLogService.logEvent(
                UUID.fromString(tenantId),
                UUID.fromString(userId),
                "APPROVAL_GRANTED",
                "APPROVAL_REQUEST",
                requestId,
                null,
                body != null ? body.toString() : "{}"
        );

        return ResponseEntity.ok(Map.of("status", "approved", "request_id", requestId));
    }

    @PostMapping("/{id}/reject")
    @PreAuthorize("hasAnyRole('OWNER', 'ADMIN')")
    public ResponseEntity<Map<String, Object>> rejectAction(
            @PathVariable("id") String requestId,
            @RequestBody(required = false) Map<String, Object> body) {

        String tenantId = TenantContext.getTenantId();
        String userId = TenantContext.getUserId();

        auditLogService.logEvent(
                UUID.fromString(tenantId),
                UUID.fromString(userId),
                "APPROVAL_REJECTED",
                "APPROVAL_REQUEST",
                requestId,
                null,
                body != null ? body.toString() : "{}"
        );

        return ResponseEntity.ok(Map.of("status", "rejected", "request_id", requestId));
    }
}
