# Architecture Specification — Enterprise AI Worker

## Overview

Enterprise AI Worker uses a decoupled, dual-service architecture designed for security, scalability, and maintainability:

1. **Spring Boot Gateway (Edge/Gateway Service)**:
   - Manages tenant lifecycle, user authentication (OIDC/OAuth2), RBAC policy enforcement, request auditing, rate limiting, and database migrations via Flyway.
   - Proxies authenticated requests to the AI Orchestration layer and relays Server-Sent Events (SSE) token streams to client applications (Web, Slack, Gmail add-on, CLI).

2. **FastAPI Agent Orchestration Service**:
   - Executes multi-agent LangGraph workflows, manages working memory and long-term memory retrieval, calls specialized sub-agents, and invokes tools via MCP (Model Context Protocol).
   - Provides streaming token and status trace endpoints over SSE/WebSocket.

3. **Data Layer**:
   - **PostgreSQL 16 + pgvector**: Stores tenants, users, roles, conversations, audit logs, and document chunk embeddings.
   - **Redis 7**: Distributed session cache, rate limiting, short-term memory, and inter-service streaming queues.
   - **MinIO / S3**: Object storage for document uploads and task artifacts.

## System Topology & Flow

```
[ Client / Web / Slack ]
          │
          │ HTTPS / SSE
          ▼
┌─────────────────────────────────────────┐
│        Spring Boot Edge Gateway         │
│  - AuthN (JWT / OIDC)                   │
│  - AuthZ / RBAC Enforcement             │
│  - Tenant Isolation (TenantContext)     │
│  - Audit Log Service                    │
└────────────────────┬────────────────────┘
                     │ Internal Service Token (signed JWT)
                     ▼
┌─────────────────────────────────────────┐
│       FastAPI Agent Orchestrator        │
│  - LLM Provider Interface               │
│  - LangGraph Planner & Specialists      │
│  - MCP Tool Server Integration          │
└─────────────────────────────────────────┘
```
