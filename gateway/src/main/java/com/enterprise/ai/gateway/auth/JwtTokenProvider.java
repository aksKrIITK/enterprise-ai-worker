package com.enterprise.ai.gateway.auth;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.UUID;

@Component
public class JwtTokenProvider {

    private final SecretKey jwtSecretKey;
    private final SecretKey serviceTokenSecretKey;

    public JwtTokenProvider(
            @Value("${gateway.security.jwt-secret}") String jwtSecret,
            @Value("${gateway.security.service-token-secret}") String serviceSecret) {
        this.jwtSecretKey = Keys.hmacShaKeyFor(jwtSecret.getBytes(StandardCharsets.UTF_8));
        this.serviceTokenSecretKey = Keys.hmacShaKeyFor(serviceSecret.getBytes(StandardCharsets.UTF_8));
    }

    public String generateUserToken(UUID userId, UUID tenantId, String email, UserRole role) {
        long expirationMs = 86400000; // 24 hours
        return Jwts.builder()
                .subject(userId.toString())
                .claim("tenant_id", tenantId.toString())
                .claim("email", email)
                .claim("role", role.name())
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + expirationMs))
                .signWith(jwtSecretKey)
                .compact();
    }

    public String generateInternalServiceToken(String tenantId, String userId, String role) {
        long expirationMs = 300000; // 5 minutes
        return Jwts.builder()
                .subject("gateway-service")
                .claim("tenant_id", tenantId)
                .claim("user_id", userId)
                .claim("role", role)
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + expirationMs))
                .signWith(serviceTokenSecretKey)
                .compact();
    }

    public Claims parseUserToken(String token) {
        return Jwts.parser()
                .verifyWith(jwtSecretKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    public boolean validateUserToken(String token) {
        try {
            parseUserToken(token);
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
