import pytest
from app.sql.sql_validator import SQLValidator
from app.agents.sql_agent import SQLAgent
from app.graph.state import AgentInput


def test_sql_validator_rejects_ddl_dml():
    forbidden_queries = [
        "DELETE FROM users WHERE id = '123'",
        "DROP TABLE tenants",
        "INSERT INTO users (id, email) VALUES ('1', 'bad@test.com')",
        "UPDATE users SET role = 'OWNER'",
        "ALTER TABLE users ADD COLUMN hacker TEXT",
    ]

    for q in forbidden_queries:
        is_valid, _, err = SQLValidator.validate_and_sanitize(q, tenant_id="tenant-1")
        assert not is_valid
        assert "Forbidden SQL operation" in err or "Only SELECT" in err


def test_sql_validator_injects_tenant_predicate_and_limit():
    raw_query = "SELECT id, email FROM users"
    is_valid, sanitized_sql, err = SQLValidator.validate_and_sanitize(raw_query, tenant_id="tenant-alpha", max_rows=100)

    assert is_valid
    assert "WHERE tenant_id = 'tenant-alpha'" in sanitized_sql
    assert "LIMIT 100" in sanitized_sql


@pytest.mark.asyncio
async def test_sql_agent_execution():
    agent = SQLAgent()
    agent_input = AgentInput(
        task_id="task-sql-1",
        tenant_id="tenant-acme",
        user_id="user-admin",
        instruction="Show conversations for my tenant",
        conversation_id="conv-sql-100",
    )

    output = await agent.run(agent_input)

    assert output.status == "success"
    assert "generated_sql" in output.result
    assert "WHERE tenant_id = 'tenant-acme'" in output.result["generated_sql"]
    assert output.result["row_count"] > 0
    assert len(output.tool_calls) == 1
    assert output.tool_calls[0].tool_name == "sql_execute_query"
