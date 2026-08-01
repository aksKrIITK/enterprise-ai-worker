# 🗄️ MySQL Multi-Tenant Isolation & User Info Database

This directory contains the MySQL 8.0+ schema definitions, seed data, and container configurations for multi-tenant isolation and user profile management in **Enterprise AI Worker**.

---

## 🏗️ Architecture & Isolation Principles

### 1. Row-Level Multi-Tenant Discriminator (`tenant_id`)
Every tenant-scoped table (`users`, `tenant_users`, `user_profiles`, `user_sessions`, `tenant_settings`, `tenant_isolation_audit`) enforces a mandatory `tenant_id CHAR(36)` column.

### 2. Composite Key Strategy
To guarantee strict tenant isolation without accidental cross-tenant data leaks:
- `users`: `UNIQUE KEY uk_tenant_user_email (primary_tenant_id, email)` ensures an email address is unique within a tenant context.
- `tenant_users`: `PRIMARY KEY (tenant_id, user_id)` maps users to tenants with tenant-scoped roles (`OWNER`, `ADMIN`, `MEMBER`, `VIEWER`, `GUEST`).
- `user_profiles`: Bounded to `tenant_id` and `user_id` with index `idx_user_profiles_tenant (tenant_id)`.
- `user_sessions`: Scoped by `tenant_id` and `user_id` to allow instant session termination per tenant.

### 3. Cascading Foreign Key Integrity
Deleting a tenant automatically cascades deletes across `tenant_settings`, `users`, `tenant_users`, `user_profiles`, `user_sessions`, and `tenant_isolation_audit`.

---

## 📁 Directory Structure

```
infra/mysql/
├── docker-compose.mysql.yml                 # Docker Compose configuration for MySQL 8.0
├── init/
│   ├── 01_schema_multitenant_userinfo.sql   # DDL tables, foreign keys, indexes, triggers
│   └── 02_seed_data.sql                     # Test tenants, users, roles, settings & audit logs
└── README.md                                # System documentation & query examples
```

---

## 🚀 Running with Docker

To start the MySQL 8.0 instance with automated schema initialization:

```bash
cd infra/mysql
docker-compose -f docker-compose.mysql.yml up -d
```

### Database Credentials

- **Host**: `localhost` (Port `3306`)
- **Database**: `enterprise_ai_mysql`
- **User**: `mysql_user`
- **Password**: `mysql_password`
- **Root Password**: `mysql_root_password`

---

## 🔍 Multi-Tenant Query Isolation Examples

### 1. Fetch User Profile with Tenant Boundary Enforcement
```sql
SELECT 
    u.id AS user_id,
    u.email,
    p.first_name,
    p.last_name,
    tu.role,
    t.name AS tenant_name
FROM users u
JOIN tenant_users tu ON u.id = tu.user_id AND tu.tenant_id = :tenant_id
JOIN user_profiles p ON u.id = p.user_id AND p.tenant_id = :tenant_id
JOIN tenants t ON tu.tenant_id = t.id
WHERE u.primary_tenant_id = :tenant_id AND u.is_active = 1;
```

### 2. Verify Multi-Tenant Guest Membership Access
```sql
SELECT 
    t.name AS tenant_name,
    tu.role,
    tu.status
FROM tenant_users tu
JOIN tenants t ON tu.tenant_id = t.id
WHERE tu.user_id = :user_id AND tu.status = 'ACTIVE';
```

### 3. Active Tenant Session Validation
```sql
SELECT 
    s.id AS session_id,
    s.tenant_id,
    s.user_id,
    s.expires_at
FROM user_sessions s
WHERE s.session_token = :token 
  AND s.tenant_id = :tenant_id 
  AND s.expires_at > NOW(6);
```
