from app.agents.base_agent import BaseAgent
from app.graph.state import AgentInput, AgentOutput, ToolCallLog
from app.sql.sql_validator import SQLValidator
from app.mcp.mcp_client import MCPClient
from datetime import datetime, timezone


class SQLAgent(BaseAgent):
    def __init__(self):
        self.mcp_client = MCPClient()

    @property
    def name(self) -> str:
        return "sql_agent"

    def generate_candidate_sql(self, instruction: str) -> str:
        """Convert natural language request to candidate SQL query based on database schema."""
        inst_lower = instruction.lower()
        if "user" in inst_lower:
            return "SELECT id, email, role, created_at FROM users"
        elif "audit" in inst_lower or "log" in inst_lower:
            return "SELECT id, actor_id, action, resource_type, created_at FROM audit_log ORDER BY created_at DESC"
        elif "conversation" in inst_lower or "chat" in inst_lower:
            return "SELECT id, title, created_at FROM conversations ORDER BY created_at DESC"
        else:
            return "SELECT id, title, created_at FROM conversations"

    async def run(self, input_data: AgentInput) -> AgentOutput:
        candidate_sql = self.generate_candidate_sql(input_data.instruction)

        # Validate through SQL Sandbox
        is_valid, sanitized_sql, error_msg = SQLValidator.validate_and_sanitize(
            candidate_sql, tenant_id=input_data.tenant_id, max_rows=100
        )

        if not is_valid:
            return AgentOutput(
                task_id=input_data.task_id,
                status="failed",
                result={"error": error_msg, "candidate_sql": candidate_sql},
                tokens_used=10,
            )

        # Execute read-only query via MCP server
        query_res = await self.mcp_client.execute_tool(
            "sql_execute_query",
            {"query": sanitized_sql, "tenant_id": input_data.tenant_id},
        )

        tool_log = ToolCallLog(
            tool_name="sql_execute_query",
            input_params={"query": sanitized_sql, "tenant_id": input_data.tenant_id},
            output_result=query_res,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        return AgentOutput(
            task_id=input_data.task_id,
            status="success",
            result={
                "generated_sql": sanitized_sql,
                "row_count": query_res.get("row_count", 0),
                "data": query_res.get("data", []),
            },
            tokens_used=20,
            tool_calls=[tool_log],
        )
