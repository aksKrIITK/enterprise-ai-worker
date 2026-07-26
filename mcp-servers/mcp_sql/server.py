from typing import Dict, Any, List


class SQLMCPServer:
    """MCP Server providing scoped, read-only SQL query execution."""

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
    async def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name == "sql_execute_query":
            query = params.get("query", "")
            tenant_id = params.get("tenant_id", "")

            # Simulated read-only execution result set for Phase 3
            mock_rows = [
                {"id": "conv-101", "tenant_id": tenant_id, "title": "Quarterly Roadmap Discussion", "messages_count": 14},
                {"id": "conv-102", "tenant_id": tenant_id, "title": "Security Compliance Audit", "messages_count": 8},
                {"id": "conv-103", "tenant_id": tenant_id, "title": "Database Optimization Sync", "messages_count": 22},
            ]
            return {
                "status": "success",
                "executed_query": query,
                "row_count": len(mock_rows),
                "data": mock_rows,
            }
        else:
            raise ValueError(f"Unknown SQL tool: {tool_name}")
