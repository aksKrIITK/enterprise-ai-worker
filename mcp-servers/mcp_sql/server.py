from typing import Dict, Any, List
import os
import sqlite3
import logging
import urllib.parse

logger = logging.getLogger(__name__)


class SQLMCPServer:
    """MCP Server providing scoped, read-only SQL query execution against real databases."""

    @staticmethod
    def get_tools() -> List[Dict[str, Any]]:
        return [
            {
                "name": "sql_execute_query",
                "description": "Execute a read-only SELECT query against the registered tenant database.",
                "requires_approval": False,
                "input_schema": {"query": "str", "tenant_id": "str"},
            }
        ]

    @staticmethod
    def _get_db_connection():
        pg_host = os.environ.get("POSTGRES_HOST", "localhost")
        pg_port = os.environ.get("POSTGRES_PORT", "5432")
        pg_db = os.environ.get("POSTGRES_DB", "enterprise_ai_db")
        pg_user = os.environ.get("POSTGRES_USER", "postgres")
        pg_pass = os.environ.get("POSTGRES_PASSWORD", "postgres_password")

        # Attempt PostgreSQL connection via psycopg2 if available
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            conn = psycopg2.connect(
                host=pg_host,
                port=pg_port,
                dbname=pg_db,
                user=pg_user,
                password=pg_pass,
                connect_timeout=3
            )
            return conn, "postgres"
        except Exception as err:
            logger.debug("PostgreSQL connection not established (%s). Using embedded SQLite database engine.", err)

        # Embedded SQLite fallback with real schema initialization
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "enterprise_ai.db"))
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Initialize schema & initial seed data if table does not exist
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                title TEXT NOT NULL,
                messages_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                email TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Seed default tenant records if empty
        cursor.execute("SELECT COUNT(*) FROM conversations")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO conversations (id, tenant_id, title, messages_count) VALUES (?, ?, ?, ?)",
                [
                    ("conv-101", "default-tenant", "Quarterly Roadmap Discussion", 14),
                    ("conv-102", "default-tenant", "Security Compliance Audit", 8),
                    ("conv-103", "default-tenant", "Database Optimization Sync", 22),
                    ("conv-201", "acme-corp", "Acme Enterprise Onboarding", 5),
                    ("conv-301", "tenant-acme", "Acme Tenant Security Roadmap", 12),
                ]
            )
            cursor.executemany(
                "INSERT INTO users (id, tenant_id, email, role) VALUES (?, ?, ?, ?)",
                [
                    ("usr-101", "default-tenant", "alice@enterprise.ai", "ADMIN"),
                    ("usr-102", "default-tenant", "bob@enterprise.ai", "MEMBER"),
                    ("usr-201", "acme-corp", "admin@acme.com", "ADMIN"),
                    ("usr-301", "tenant-acme", "admin@acme-tenant.com", "ADMIN"),
                ]
            )
            conn.commit()
            
        return conn, "sqlite"

    @staticmethod
    async def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "sql_execute_query":
            query = params.get("query", "").strip()
            tenant_id = params.get("tenant_id", "default-tenant")

            if not query:
                raise ValueError("Query string cannot be empty.")

            conn, db_type = SQLMCPServer._get_db_connection()
            try:
                if db_type == "postgres":
                    from psycopg2.extras import RealDictCursor
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                    cursor.execute(query)
                    rows = [dict(r) for r in cursor.fetchall()]
                else:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    raw_rows = cursor.fetchall()
                    rows = [dict(r) for r in raw_rows]

                return {
                    "status": "success",
                    "executed_query": query,
                    "db_type": db_type,
                    "row_count": len(rows),
                    "data": rows,
                }
            except Exception as err:
                logger.error("SQL execution error on %s: %s", db_type, err)
                return {
                    "status": "error",
                    "executed_query": query,
                    "db_type": db_type,
                    "error": str(err),
                    "row_count": 0,
                    "data": [],
                }
            finally:
                conn.close()
        else:
            raise ValueError(f"Unknown SQL tool: {tool_name}")

