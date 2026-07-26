package com.enterprise.ai.gateway.approval;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface ApprovalRequestRepository extends JpaRepository<ApprovalRequest, UUID> {
    List<ApprovalRequest> findByTenantIdAndStatusOrderByCreatedAtDesc(UUID tenantId, String status);
}
