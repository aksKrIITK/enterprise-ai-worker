-- ==============================================================================
-- Enterprise AI Worker - MySQL Multi-Tenant Isolation & User Info Schema
-- Database Engine: MySQL 8.0+
-- Charset: utf8mb4, Collation: utf8mb4_unicode_ci
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS enterprise_ai_mysql 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE enterprise_ai_mysql;

-- Disable Foreign Key Checks during setup
SET FOREIGN_KEY_CHECKS = 0;

-- ------------------------------------------------------------------------------
-- 1. Master Tenants Table
-- Core tenant organization registry representing isolated customer accounts.
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS tenant_settings;
DROP TABLE IF EXISTS tenant_isolation_audit;
DROP TABLE IF EXISTS user_sessions;
DROP TABLE IF EXISTS user_profiles;
DROP TABLE IF EXISTS tenant_users;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS tenants;

CREATE TABLE tenants (
    id CHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    plan ENUM('FREE', 'STANDARD', 'PROFESSIONAL', 'ENTERPRISE') NOT NULL DEFAULT 'STANDARD',
    status ENUM('ACTIVE', 'SUSPENDED', 'PENDING_DELETION') NOT NULL DEFAULT 'ACTIVE',
    max_users INT NOT NULL DEFAULT 50,
    data_residency VARCHAR(50) NOT NULL DEFAULT 'US',
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_tenants_slug (slug),
    KEY idx_tenants_status (status),
    KEY idx_tenants_plan (plan)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 2. Tenant Settings Table
-- Per-tenant security policy, SSO details, and feature flags.
-- ------------------------------------------------------------------------------
CREATE TABLE tenant_settings (
    tenant_id CHAR(36) NOT NULL,
    sso_enabled TINYINT(1) NOT NULL DEFAULT 0,
    sso_provider VARCHAR(50) NULL,
    sso_config JSON NULL,
    mfa_required TINYINT(1) NOT NULL DEFAULT 0,
    allowed_ip_ranges JSON NULL,
    feature_flags JSON NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    
    PRIMARY KEY (tenant_id),
    CONSTRAINT fk_tenant_settings_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 3. Core Users Table
-- Primary authentication identities bounded to a primary tenant context.
-- ------------------------------------------------------------------------------
CREATE TABLE users (
    id CHAR(36) NOT NULL,
    primary_tenant_id CHAR(36) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    email_verified TINYINT(1) NOT NULL DEFAULT 0,
    mfa_enabled TINYINT(1) NOT NULL DEFAULT 0,
    mfa_secret VARCHAR(255) NULL,
    last_login_at DATETIME(6) NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_tenant_user_email (primary_tenant_id, email),
    KEY idx_users_email (email),
    KEY idx_users_primary_tenant (primary_tenant_id),
    CONSTRAINT fk_users_primary_tenant FOREIGN KEY (primary_tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 4. Tenant Users Table (Multi-Tenant Memberships & RBAC)
-- Many-to-Many mapping enabling multi-tenancy access with tenant-scoped roles.
-- Composite Primary Key (tenant_id, user_id) enforces row-level multi-tenant scope.
-- ------------------------------------------------------------------------------
CREATE TABLE tenant_users (
    tenant_id CHAR(36) NOT NULL,
    user_id CHAR(36) NOT NULL,
    role ENUM('OWNER', 'ADMIN', 'MEMBER', 'VIEWER', 'GUEST') NOT NULL DEFAULT 'MEMBER',
    status ENUM('ACTIVE', 'INVITED', 'SUSPENDED') NOT NULL DEFAULT 'ACTIVE',
    joined_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    
    PRIMARY KEY (tenant_id, user_id),
    KEY idx_tenant_users_user (user_id),
    KEY idx_tenant_users_role (tenant_id, role),
    KEY idx_tenant_users_status (tenant_id, status),
    CONSTRAINT fk_tenant_users_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE,
    CONSTRAINT fk_tenant_users_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 5. User Profiles Table (Extended User Info)
-- Tenant-isolated profile information, preferences, department, and contact details.
-- ------------------------------------------------------------------------------
CREATE TABLE user_profiles (
    user_id CHAR(36) NOT NULL,
    tenant_id CHAR(36) NOT NULL,
    first_name VARCHAR(100) NULL,
    last_name VARCHAR(100) NULL,
    display_name VARCHAR(200) NULL,
    phone_number VARCHAR(50) NULL,
    department VARCHAR(100) NULL,
    job_title VARCHAR(100) NULL,
    avatar_url TEXT NULL,
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    locale VARCHAR(10) NOT NULL DEFAULT 'en-US',
    preferences JSON NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    
    PRIMARY KEY (user_id),
    KEY idx_user_profiles_tenant (tenant_id),
    KEY idx_user_profiles_dept (tenant_id, department),
    CONSTRAINT fk_user_profiles_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_user_profiles_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 6. User Sessions Table (Tenant-Scoped Session & Token Isolation)
-- Active user session records bound to both user and active tenant context.
-- ------------------------------------------------------------------------------
CREATE TABLE user_sessions (
    id CHAR(36) NOT NULL,
    tenant_id CHAR(36) NOT NULL,
    user_id CHAR(36) NOT NULL,
    session_token VARCHAR(255) NOT NULL,
    refresh_token VARCHAR(255) NULL,
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    expires_at DATETIME(6) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    last_accessed_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_session_token (session_token),
    KEY idx_user_sessions_tenant_user (tenant_id, user_id),
    KEY idx_user_sessions_expires (expires_at),
    CONSTRAINT fk_user_sessions_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE,
    CONSTRAINT fk_user_sessions_user FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 7. Tenant Isolation Audit Log Table
-- Audit trail dedicated to capturing tenant boundary events and security access logs.
-- ------------------------------------------------------------------------------
CREATE TABLE tenant_isolation_audit (
    id CHAR(36) NOT NULL,
    tenant_id CHAR(36) NOT NULL,
    actor_id CHAR(36) NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255) NULL,
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    payload_summary JSON NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    
    PRIMARY KEY (id),
    KEY idx_audit_tenant_created (tenant_id, created_at),
    KEY idx_audit_actor (actor_id),
    CONSTRAINT fk_tenant_audit_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE,
    CONSTRAINT fk_tenant_audit_actor FOREIGN KEY (actor_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Re-enable Foreign Key Checks
SET FOREIGN_KEY_CHECKS = 1;
