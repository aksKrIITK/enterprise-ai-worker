package com.enterprise.ai.gateway.auth;

import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final JwtTokenProvider tokenProvider;

    @PostMapping("/dev-token")
    public ResponseEntity<Map<String, String>> generateDevToken(@RequestBody DevTokenRequest request) {
        UUID userId = request.getUserId() != null ? UUID.fromString(request.getUserId()) : UUID.randomUUID();
        UUID tenantId = request.getTenantId() != null ? UUID.fromString(request.getTenantId()) : UUID.randomUUID();
        String email = request.getEmail() != null ? request.getEmail() : "dev@enterprise.ai";
        UserRole role = request.getRole() != null ? UserRole.valueOf(request.getRole()) : UserRole.ADMIN;

        String token = tokenProvider.generateUserToken(userId, tenantId, email, role);

        return ResponseEntity.ok(Map.of(
                "token", token,
                "user_id", userId.toString(),
                "tenant_id", tenantId.toString(),
                "email", email,
                "role", role.name()
        ));
    }

    @Data
    public static class DevTokenRequest {
        private String userId;
        private String tenantId;
        private String email;
        private String role;
    }
}
