# Security Model & Multi-Tenancy — Enterprise AI Worker

## Security Principles

1. **Secure by Default**: Every API endpoint defaults to requiring authentication and tenant context.
2. **Multi-Tenancy Isolation**:
   - Every database table incorporates `tenant_id`.
   - PostgreSQL Row-Level Security (RLS) policies enforce cross-tenant data boundaries at the database level.
   - Vector similarity searches and knowledge graph queries are strictly filtered by `tenant_id`.
3. **Role-Based Access Control (RBAC)**:
   - User Roles: `OWNER`, `ADMIN`, `MEMBER`, `VIEWER`.
   - Capabilities: `can_send_email`, `can_merge_pr`, `can_run_sql`, `can_manage_users`.
   - Enforced at both the Gateway layer and re-checked at the Tool Call layer before executing any tool or agent action.
4. **Human-in-the-Loop Gateways**:
   - All state-changing or external write operations (sending email, executing DML/DDL SQL, opening/merging pull requests) pause agent execution and emit an `ApprovalRequest`.
5. **Immutable Audit Logging**:
   - Every security-sensitive action, data query, tool invocation, and approval decision writes an immutable entry to `audit_log` with `tenant_id`, `actor_id`, `action`, `resource_type`, and timestamps.
