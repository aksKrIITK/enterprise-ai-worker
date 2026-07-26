package com.enterprise.ai.gateway;

import com.enterprise.ai.gateway.auth.JwtTokenProvider;
import com.enterprise.ai.gateway.auth.UserRole;
import io.jsonwebtoken.Claims;
import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

class GatewayApplicationTests {

    private final JwtTokenProvider tokenProvider = new JwtTokenProvider(
            "super_secret_jwt_key_for_enterprise_ai_worker_gateway_2026_production_secure_min_32_chars",
            "super_secret_jwt_service_token_gateway_to_orchestrator_internal_communication"
    );

    @Test
    void testUserTokenGenerationAndParsing() {
        UUID userId = UUID.randomUUID();
        UUID tenantId = UUID.randomUUID();
        String email = "test@enterprise.ai";
        UserRole role = UserRole.ADMIN;

        String token = tokenProvider.generateUserToken(userId, tenantId, email, role);
        assertNotNull(token);
        assertTrue(tokenProvider.validateUserToken(token));

        Claims claims = tokenProvider.parseUserToken(token);
        assertEquals(userId.toString(), claims.getSubject());
        assertEquals(tenantId.toString(), claims.get("tenant_id", String.class));
        assertEquals(email, claims.get("email", String.class));
        assertEquals("ADMIN", claims.get("role", String.class));
    }

    @Test
    void testInternalServiceTokenGeneration() {
        String tenantId = UUID.randomUUID().toString();
        String userId = UUID.randomUUID().toString();
        String role = "MEMBER";

        String serviceToken = tokenProvider.generateInternalServiceToken(tenantId, userId, role);
        assertNotNull(serviceToken);
    }
}
