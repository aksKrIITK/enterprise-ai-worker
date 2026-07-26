package com.enterprise.ai.gateway.audit;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
public class AuditLogService {

    @org.springframework.beans.factory.annotation.Autowired(required = false)
    private AuditLogRepository auditLogRepository;

    @Transactional
    public AuditLog logEvent(UUID tenantId, UUID actorId, String action, String resourceType, String resourceId, String beforeState, String afterState) {
        AuditLog entry = AuditLog.builder()
                .tenantId(tenantId)
                .actorId(actorId)
                .action(action)
                .resourceType(resourceType)
                .resourceId(resourceId)
                .beforeState(beforeState)
                .afterState(afterState)
                .build();
        if (auditLogRepository != null) {
            return auditLogRepository.save(entry);
        }
        return entry;
    }
}

