package com.enterprise.ai.gateway.tenant;

import com.enterprise.ai.gateway.auth.JwtTokenProvider;
import com.enterprise.ai.gateway.auth.UserPrincipal;
import com.enterprise.ai.gateway.auth.UserRole;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.UUID;

/**
 * Filter responsible for extracting tenant identity and security authentication
 * context from Authorization HTTP headers on every incoming request.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class TenantFilter extends OncePerRequestFilter {

    private final JwtTokenProvider tokenProvider;

    @Override
    protected void doFilterInternal(
            @NonNull HttpServletRequest request,
            @NonNull HttpServletResponse response,
            @NonNull FilterChain filterChain) throws ServletException, IOException {

        log.trace("TenantFilter processing request to URI: {}", request.getRequestURI());

        try {
            String jwt = getJwtFromRequest(request);

            if (StringUtils.hasText(jwt)) {
                if (tokenProvider.validateUserToken(jwt)) {
                    try {
                        Claims claims = tokenProvider.parseUserToken(jwt);
                        String userIdStr = claims.getSubject();
                        String tenantIdStr = claims.get("tenant_id", String.class);
                        String email = claims.get("email", String.class);
                        String roleStr = claims.get("role", String.class);

                        UserRole role = UserRole.valueOf(roleStr);
                        UUID userId = UUID.fromString(userIdStr);
                        UUID tenantId = UUID.fromString(tenantIdStr);

                        // Populate ThreadLocal TenantContext for multi-tenant isolation
                        TenantContext.setTenantId(tenantIdStr);
                        TenantContext.setUserId(userIdStr);
                        TenantContext.setUserRole(roleStr);

                        // Build Spring Security Principal and Authentication token
                        UserPrincipal principal = new UserPrincipal(userId, tenantId, email, role);
                        UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                                principal, null, principal.getAuthorities()
                        );
                        SecurityContextHolder.getContext().setAuthentication(authentication);

                        log.debug("Successfully authenticated request for user [{}] under tenant [{}] with role [{}]",
                                userIdStr, tenantIdStr, roleStr);
                    } catch (JwtException | IllegalArgumentException e) {
                        log.warn("Failed to parse valid JWT token claims: {}", e.getMessage());
                    }
                } else {
                    log.warn("JWT token validation failed for request to: {}", request.getRequestURI());
                }
            } else {
                log.trace("No Bearer JWT token present in request header.");
            }

            filterChain.doFilter(request, response);
        } catch (Exception e) {
            log.error("Unhandled exception in TenantFilter: {}", e.getMessage(), e);
            throw e;
        } finally {
            // Ensure ThreadLocal context cleanup to prevent tenant leakage across pooled worker threads
            TenantContext.clear();
            log.trace("Cleared TenantContext ThreadLocal variables.");
        }
    }

    /**
     * Extracts Bearer token string from HTTP Authorization header.
     */
    private String getJwtFromRequest(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}

