# 🚀 Enterprise AI Worker

> **Production-Grade, Multi-Tenant, Multi-Agent AI Employee Platform**

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3.2-green.svg)](https://spring.io/projects/spring-boot)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-blue.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-38B2AC.svg)](https://tailwindcss.com/)

**Enterprise AI Worker** is a multi-tenant SaaS platform that gives every company an "AI employee": an intelligent assistant that integrates into Slack, email, GitHub, Jira, databases, and internal documents. Unlike simple chatbot wrappers, it uses a stateful **Supervisor + Specialist Multi-Agent System** (powered by LangGraph), **MCP (Model Context Protocol)** tool connectors, **pgvector ACL RAG**, **long-term memory consolidation**, and **Human-in-the-Loop (HITL) approval gates** for state-changing operations.

---

## 🏗️ Architecture

Enterprise AI Worker uses a decoupled, dual-stack backend topology:

```
                            ┌─────────────────────────────────┐
                            │   React 18 + TS Web Frontend    │
                            │  (Real-Time SSE, HITL Approval) │
                            └────────────────┬────────────────┘
                                             │ HTTPS / SSE
                       ┌─────────────────────▼──────────────────────┐
                       │    Spring Boot Edge Gateway (Java 17/21)   │
                       │  - AuthN (JWT / OIDC), RBAC Enforcement    │
                       │  - Multi-Tenant Isolation (TenantContext)  │
                       │  - Flyway Migrations & Immutable Audit Log │
                       └─────────────────────┬──────────────────────┘
                                             │ Signed Service Token (JWT)
                       ┌─────────────────────▼──────────────────────┐
                       │  FastAPI Agent Orchestrator (Python 3.12) │
                       │  - LangGraph Planner (Supervisor)         │
                       │  - Specialist Workers (Doc, Research, SQL, │
                       │    Email, Coding Agents)                   │
                       │  - Long-Term Memory & ACL Retriever        │
                       └─────┬───────────┬───────────┬───────────┬──┘
                             │           │           │           │
              ┌──────────────┘       ┌───┘       └───┐       └───┐
              ▼                      ▼               ▼           ▼
       ┌─────────────┐       ┌──────────────┐  ┌───────────┐ ┌────────┐
       │ MCP Servers │       │ PostgreSQL16 │  │ Vector DB │ │ Redis  │
       │ Slack/Gmail/│       │ (Tenants,    │  │ (pgvector)│ │ Cache/ │
       │ Jira/GitHub/│       │  Users, Audit│  └───────────┘ │ Streams│
       │ Calendar/SQL│       └──────────────┘                └────────┘
       └─────────────┘
```

### Key Technical Pillars

1. **Spring Boot Gateway (Port 8080)**: Handles JWT authentication, `TenantContext` isolation, RBAC role enforcement (`OWNER`, `ADMIN`, `MEMBER`, `VIEWER`), Flyway database schema migrations, and immutable audit logging.
2. **FastAPI Agent Orchestrator (Port 8000)**: Coordinates stateful graph execution using **LangGraph**. Decomposes complex user instructions into subtasks, delegates to specialist agents, and streams real-time token deltas and reasoning traces over SSE.
3. **Pluggable LLM Abstraction**: Switch between OpenAI (`gpt-4o`) and Google Gemini (`gemini-2.5-flash`) via configuration without changing agent logic.
4. **Model Context Protocol (MCP)**: Exposes tools (Slack, Gmail, Calendar, SQL, Jira, GitHub) via standardized MCP servers.
5. **ACL-Aware Vector RAG**: Enforces strict dual-layer security: `WHERE tenant_id = :tenant_id` and document-level ACL permission tag filtering.
6. **Human-in-the-Loop Approval Workflow**: All write/external operations (`send_email`, `github_open_pr`, SQL modifications) pause execution at a checkpoint and generate an `ApprovalRequest`. Resumes graph state seamlessly upon approval.
7. **SOC2-Track Immutable Audit Logging**: Records every tool call, approval decision, document query, and SQL execution with distributed `X-Trace-Id` correlation headers.

---

## 🔑 Environment Variables & Live Credentials (`.env`)

To run **Enterprise AI Worker** in production connected to real LLMs and external services, configure your `.env` file in the root workspace (and `orchestrator/.env`):

```ini
# ==============================================================================
# 1. LLM PROVIDER API KEYS (At least one required for real AI completions)
# ==============================================================================
DEFAULT_LLM_PROVIDER=openai

# OpenAI API Key (Get from: https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-proj-YOUR_REAL_OPENAI_API_KEY_HERE
OPENAI_MODEL=gpt-4o

# Google Gemini API Key (Get from: https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=AIzaSy_YOUR_REAL_GEMINI_API_KEY_HERE
GEMINI_MODEL=gemini-2.5-flash

# ==============================================================================
# 2. INFRASTRUCTURE & DATABASE URLS
# ==============================================================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=enterprise_ai_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres_password

SPRING_DATASOURCE_URL=jdbc:postgresql://localhost:5432/enterprise_ai_db

REDIS_HOST=localhost
REDIS_PORT=6379

MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minio_admin
MINIO_SECRET_KEY=minio_password
MINIO_BUCKET=enterprise-ai-artifacts

# ==============================================================================
# 3. SERVICE SECURITY & JWT SIGNING KEYS
# ==============================================================================
JWT_SECRET=super_secret_jwt_key_min_32_characters_for_production_security_2026
SERVICE_TO_SERVICE_SECRET=super_secret_internal_jwt_service_token_between_gateway_and_orchestrator

# ==============================================================================
# 4. EXTERNAL INTEGRATION API KEYS & OAUTH CREDENTIALS (MCP Tool Servers)
# ==============================================================================
# GitHub Personal Access Token (Scopes: repo, workflow, read:org)
GITHUB_TOKEN=ghp_YOUR_REAL_GITHUB_PERSONAL_ACCESS_TOKEN

# Atlassian Jira API Credentials (https://id.atlassian.com/manage-profile/security/api-tokens)
JIRA_URL=https://your-company.atlassian.net
JIRA_USER_EMAIL=your-email@company.com
JIRA_API_TOKEN=ATATT3xFfGF0_YOUR_REAL_JIRA_API_TOKEN

# Slack Bot User OAuth Token (Scopes: channels:read, chat:write)
SLACK_BOT_TOKEN=xoxb-YOUR_REAL_SLACK_BOT_TOKEN
SLACK_SIGNING_SECRET=YOUR_REAL_SLACK_SIGNING_SECRET

# Google OAuth 2.0 Credentials (Gmail & Calendar API)
GOOGLE_CLIENT_ID=YOUR_REAL_GOOGLE_CLIENT_ID.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-YOUR_REAL_GOOGLE_CLIENT_SECRET
GOOGLE_REFRESH_TOKEN=YOUR_REAL_GOOGLE_OAUTH_REFRESH_TOKEN
```

---

## ⚡ Quickstart & Live Run Guide

### Step 1: Clone Repository & Configure `.env`

```bash
git clone https://github.com/your-username/enterprise-ai-worker.git
cd enterprise-ai-worker

# Edit .env with your real OpenAI / Gemini / GitHub / Jira API keys
cp .env.example .env
```

---

### Step 2: Start PostgreSQL 16 (pgvector), Redis & MinIO

```bash
# Start PostgreSQL (pgvector), Redis 7, and MinIO S3 object storage
docker-compose -f infra/docker/docker-compose.yml up -d
```

---

### Step 3: Launch FastAPI Agent Orchestrator (Port 8000)

```bash
cd orchestrator

# Install Python dependencies
pip install -r requirements.txt

# Run pytest test suite to verify installation
python -m pytest

# Start FastAPI server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

### Step 4: Launch Spring Boot Edge Gateway (Port 8080)

```bash
cd ../gateway

# Set JAVA_HOME and run Maven Spring Boot
$env:JAVA_HOME="C:\Program Files\Java\jdk-17.0.20"
& "C:\Program Files\JetBrains\IntelliJ IDEA 2026.2\plugins\maven-plugin\lib\maven3\bin\mvn.cmd" spring-boot:run
```

---

### Step 5: Launch React + TypeScript Frontend (Port 3000)

```bash
cd ../frontend

# Install dependencies and start Vite dev server
npm install
npm run dev
```

Open **`http://localhost:3000`** in your browser to access the live platform UI!

---

## 🤖 Specialist Agents

| Agent | Responsibilities |
|---|---|
| **Planner (Supervisor)** | Decomposes user instructions into `SubTask` items, routes to specialists, and synthesizes final grounded answers with citations. |
| **Document Agent** | Answers chat-with-your-docs queries using ACL-filtered `pgvector` similarity search. |
| **Researcher Agent** | Performs hybrid retrieval combining document vector search with Knowledge Graph multi-hop relationship traversal. |
| **SQL Agent** | Converts natural language requests into read-only SQL queries via a strict SQL Sandbox validator (`LIMIT 100`, DDL/DML rejection, tenant predicate injection). |
| **Email Agent** | Searches, drafts, and sends emails via Gmail API with human approval gating for send actions. |
| **Coding Agent** | Inspects repositories, triages Jira issues, links commits, and drafts GitHub Pull Requests gated by human approval. |

---

## 🧪 Testing & Verification

The project includes an extensive test suite verifying tenant isolation, ACL security, approval checkpointing, and agent routing:

```bash
# Run Orchestrator Pytest Suite (27 Tests across 5 Phases)
cd orchestrator
python -m pytest -v
```

```
======================== 27 passed in 5.16s ========================
```

---

## 🛡️ Security & SOC2 Compliance

- **Tenant Isolation**: Every query enforces `WHERE tenant_id = :tenant_id` at the database and vector store level. Verified by automated prompt-injection tests (`test_tenant_isolation.py`).
- **Prompt-Injection Sanitization**: All retrieved text chunks are wrapped in `<untrusted_data>` tags and stripped of prompt hijacking patterns.
- **SQL Sandboxing**: Rejects all DDL/DML queries (`DROP`, `DELETE`, `UPDATE`, `INSERT`) and limits query output size.
- **Immutable Audit Logging**: Logs all security events with `tenant_id`, `actor_id`, `action`, and `trace_id`.

---

## 📄 License

This project is open-source under the **MIT License**. See [LICENSE](LICENSE) for details.
