-- ==============================================================================
-- Enterprise AI Worker - MySQL Multi-Tenant & User Info Seed Data
-- ==============================================================================

USE enterprise_ai_mysql;

-- Disable Foreign Key Checks for clean seeding
SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------------------------
-- 1. Seed Tenants
-- ------------------------------------------------------------------------------
INSERT INTO tenants (id, name, slug, plan, status, max_users, data_residency) VALUES
('11111111-1111-1111-1111-111111111111', 'Acme Corporation', 'acme-corp', 'ENTERPRISE', 'ACTIVE', 500, 'US'),
('22222222-2222-2222-2222-222222222222', 'Stark Industries', 'stark-industries', 'PROFESSIONAL', 'ACTIVE', 100, 'EU'),
('33333333-3333-3333-3333-333333333333', 'Cyberdyne Systems', 'cyberdyne', 'STANDARD', 'SUSPENDED', 10, 'US');

-- ------------------------------------------------------------------------------
-- 2. Seed Tenant Settings
-- ------------------------------------------------------------------------------
INSERT INTO tenant_settings (tenant_id, sso_enabled, sso_provider, sso_config, mfa_required, allowed_ip_ranges, feature_flags) VALUES
('11111111-1111-1111-1111-111111111111', 1, 'OKTA', '{"domain": "sso.acme.com", "client_id": "okta_acme_123"}', 1, '["192.168.1.0/24", "10.0.0.0/8"]', '{"ai_agent_coding": true, "rag_vector_search": true, "hitl_approval_required": true}'),
('22222222-2222-2222-2222-222222222222', 0, NULL, NULL, 0, '[]', '{"ai_agent_coding": true, "rag_vector_search": true, "hitl_approval_required": false}'),
('33333333-3333-3333-3333-333333333333', 0, NULL, NULL, 1, '[]', '{"ai_agent_coding": false}');

-- ------------------------------------------------------------------------------
-- 3. Seed Users
-- ------------------------------------------------------------------------------
INSERT INTO users (id, primary_tenant_id, email, password_hash, is_active, email_verified, mfa_enabled, last_login_at) VALUES
-- Acme Corp Users
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111', 'admin@acme.com', '$2a$12$e8Y.8jF6b/N1hX9h5K3w2eZ9/0kO.N2zR8cW6lX4mY3nO5pQ7rS6t', 1, 1, 1, '2026-08-01 10:00:00.000000'),
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '11111111-1111-1111-1111-111111111111', 'dev@acme.com', '$2a$12$e8Y.8jF6b/N1hX9h5K3w2eZ9/0kO.N2zR8cW6lX4mY3nO5pQ7rS6t', 1, 1, 0, '2026-08-01 11:30:00.000000'),

-- Stark Industries Users
('cccccccc-cccc-cccc-cccc-cccccccccccc', '22222222-2222-2222-2222-222222222222', 'tony@stark.com', '$2a$12$e8Y.8jF6b/N1hX9h5K3w2eZ9/0kO.N2zR8cW6lX4mY3nO5pQ7rS6t', 1, 1, 1, '2026-08-01 12:15:00.000000'),
('dddddddd-dddd-dddd-dddd-dddddddddddd', '22222222-2222-2222-2222-222222222222', 'pepper@stark.com', '$2a$12$e8Y.8jF6b/N1hX9h5K3w2eZ9/0kO.N2zR8cW6lX4mY3nO5pQ7rS6t', 1, 1, 0, '2026-08-01 09:45:00.000000');

-- ------------------------------------------------------------------------------
-- 4. Seed Tenant Memberships (tenant_users)
-- ------------------------------------------------------------------------------
INSERT INTO tenant_users (tenant_id, user_id, role, status) VALUES
('11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'OWNER', 'ACTIVE'),
('11111111-1111-1111-1111-111111111111', 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'MEMBER', 'ACTIVE'),
('22222222-2222-2222-2222-222222222222', 'cccccccc-cccc-cccc-cccc-cccccccccccc', 'OWNER', 'ACTIVE'),
('22222222-2222-2222-2222-222222222222', 'dddddddd-dddd-dddd-dddd-dddddddddddd', 'ADMIN', 'ACTIVE'),

-- Multi-Tenant Guest Membership Example: Tony Stark guest access in Acme Corp
('11111111-1111-1111-1111-111111111111', 'cccccccc-cccc-cccc-cccc-cccccccccccc', 'GUEST', 'ACTIVE');

-- ------------------------------------------------------------------------------
-- 5. Seed User Profiles
-- ------------------------------------------------------------------------------
INSERT INTO user_profiles (user_id, tenant_id, first_name, last_name, display_name, phone_number, department, job_title, avatar_url, timezone, preferences) VALUES
('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', '11111111-1111-1111-1111-111111111111', 'Alice', 'Admin', 'Alice (Acme Admin)', '+1-555-0101', 'IT Operations', 'VP of Engineering', 'https://avatar.example.com/alice.png', 'America/New_York', '{"theme": "dark", "notifications_enabled": true}'),
('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', '11111111-1111-1111-1111-111111111111', 'Bob', 'Developer', 'Bob Dev', '+1-555-0102', 'Software Engineering', 'Senior Staff Engineer', 'https://avatar.example.com/bob.png', 'America/Los_Angeles', '{"theme": "dark", "notifications_enabled": false}'),
('cccccccc-cccc-cccc-cccc-cccccccccccc', '22222222-2222-2222-2222-222222222222', 'Tony', 'Stark', 'Tony Stark', '+1-555-3000', 'Executive', 'Chief Executive Officer', 'https://avatar.example.com/tony.png', 'America/New_York', '{"theme": "cyberpunk", "ai_model_preference": "gpt-4o"}'),
('dddddddd-dddd-dddd-dddd-dddddddddddd', '22222222-2222-2222-2222-222222222222', 'Pepper', 'Potts', 'Pepper Potts', '+1-555-3001', 'Management', 'Chief Operating Officer', 'https://avatar.example.com/pepper.png', 'America/New_York', '{"theme": "light", "ai_model_preference": "gemini-2.5-flash"}');

-- ------------------------------------------------------------------------------
-- 6. Seed Active User Sessions
-- ------------------------------------------------------------------------------
INSERT INTO user_sessions (id, tenant_id, user_id, session_token, refresh_token, ip_address, user_agent, expires_at) VALUES
('s1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'sess_acme_alice_token_998877665544332211', 'refr_acme_alice_9988776655', '192.168.1.50', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', '2026-08-08 10:00:00.000000'),
('s2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222', 'cccccccc-cccc-cccc-cccc-cccccccccccc', 'sess_stark_tony_token_112233445566778899', 'refr_stark_tony_1122334455', '10.0.1.100', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', '2026-08-08 12:15:00.000000');

-- ------------------------------------------------------------------------------
-- 7. Seed Tenant Isolation Audit Logs
-- ------------------------------------------------------------------------------
INSERT INTO tenant_isolation_audit (id, tenant_id, actor_id, action, resource_type, resource_id, ip_address, payload_summary) VALUES
('a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'USER_LOGIN', 'USER_SESSION', 's1111111-1111-1111-1111-111111111111', '192.168.1.50', '{"login_method": "SSO_OKTA", "status": "SUCCESS"}'),
('a2222222-2222-2222-2222-222222222222', '22222222-2222-2222-2222-222222222222', 'cccccccc-cccc-cccc-cccc-cccccccccccc', 'USER_LOGIN', 'USER_SESSION', 's2222222-2222-2222-2222-222222222222', '10.0.1.100', '{"login_method": "LOCAL_MFA", "status": "SUCCESS"}');

SET FOREIGN_KEY_CHECKS = 1;
