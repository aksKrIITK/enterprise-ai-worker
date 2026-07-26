import pytest
from app.agents.coding_agent import CodingAgent
from app.graph.state import AgentInput
from app.approval.approval import ApprovalManager

approval_manager = ApprovalManager()


@pytest.fixture(autouse=True)
def clear_approvals():
    approval_manager.clear()


@pytest.mark.asyncio
async def test_coding_agent_pr_approval_gating():
    agent = CodingAgent()
    agent_input = AgentInput(
        task_id="task-code-100",
        tenant_id="tenant-dev",
        user_id="user-engineer",
        instruction="Open a PR for issue JIRA-404 on enterprise/app",
        conversation_id="conv-code-1",
    )

    output = await agent.run(agent_input)

    # Must require approval for GitHub PR creation
    assert output.status == "needs_approval"
    assert output.approval_request is not None
    assert output.approval_request["requested_action"] == "github_open_pr"

    req_id = output.approval_request["id"]
    pending = approval_manager.get_pending_requests("tenant-dev")
    assert len(pending) == 1
    assert pending[0].id == req_id


@pytest.mark.asyncio
async def test_coding_agent_jira_creation():
    agent = CodingAgent()
    agent_input = AgentInput(
        task_id="task-code-200",
        tenant_id="tenant-dev",
        user_id="user-engineer",
        instruction="Create Jira ticket for payments bug",
        conversation_id="conv-code-2",
    )

    output = await agent.run(agent_input)

    assert output.status == "success"
    assert "jira_issue" in output.result
    assert output.result["jira_issue"]["status"] == "success"
