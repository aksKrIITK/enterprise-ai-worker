package com.enterprise.ai.gateway.tenant;

import com.enterprise.ai.gateway.auth.JwtTokenProvider;
import com.enterprise.ai.gateway.auth.UserPrincipal;
import com.enterprise.ai.gateway.auth.UserRole;
import io.jsonwebtoken.Claims;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.lang.NonNull;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.UUID;

@Component
@RequiredArgsConstructor
public class TenantFilter extends OncePerRequestFilter {

    private final JwtTokenProvider tokenProvider;

    @Override
    protected void doFilterInternal(
            @NonNull HttpServletRequest request,
            @NonNull HttpServletResponse response,
            @NonNull FilterChain filterChain) throws ServletException, IOException {

        try {
            String jwt = getJwtFromRequest(request);

            if (StringUtils.hasText(jwt) && tokenProvider.validateUserToken(jwt)) {
                Claims claims = tokenProvider.parseUserToken(jwt);
                String userIdStr = claims.getSubject();
                String tenantIdStr = claims.get("tenant_id", String.class);
                String email = claims.get("email", String.class);
                String roleStr = claims.get("role", String.class);

                UserRole role = UserRole.valueOf(roleStr);
                UUID userId = UUID.fromString(userIdStr);
                UUID tenantId = UUID.fromString(tenantIdStr);

                TenantContext.setTenantId(tenantIdStr);
                TenantContext.setUserId(userIdStr);
                TenantContext.setUserRole(roleStr);

                UserPrincipal principal = new UserPrincipal(userId, tenantId, email, role);
                UsernamePasswordAuthenticationToken authentication = new UsernamePasswordAuthenticationToken(
                        principal, null, principal.getAuthorities()
                );
                SecurityContextHolder.getContext().setAuthentication(authentication);
            }
            filterChain.doFilter(request, response);
        } finally {
            TenantContext.clear();
        }
    }

    private String getJwtFromRequest(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}
