import pytest
from app.approval.approval import ApprovalManager
from app.agents.email_agent import EmailAgent
from app.graph.state import AgentInput

approval_manager = ApprovalManager()


@pytest.fixture(autouse=True)
def clear_approvals():
    approval_manager.clear()


@pytest.mark.asyncio
async def test_email_agent_gated_approval_flow():
    agent = EmailAgent()
    agent_input = AgentInput(
        task_id="task-email-1",
        tenant_id="tenant-acme",
        user_id="user-bob",
        instruction="Send an email to client@acme.com confirming 3 PM meeting",
        conversation_id="conv-email-100",
    )

    output = await agent.run(agent_input)

    # Must require approval
    assert output.status == "needs_approval"
    assert output.approval_request is not None
    req_id = output.approval_request["id"]

    # Verify stored in ApprovalManager
    pending = approval_manager.get_pending_requests("tenant-acme")
    assert len(pending) == 1
    assert pending[0].id == req_id

    # Simulate Approval Decision
    approved_req = approval_manager.approve_request(req_id, approver_id="admin-alice")
    assert approved_req.status == "approved"
    assert approved_req.approver_id == "admin-alice"


@pytest.mark.asyncio
async def test_approval_rejection_flow():
    agent = EmailAgent()
    agent_input = AgentInput(
        task_id="task-email-2",
        tenant_id="tenant-beta",
        user_id="user-charlie",
        instruction="Send an email to vendor@globex.com",
        conversation_id="conv-email-200",
    )

    output = await agent.run(agent_input)
    req_id = output.approval_request["id"]

    # Simulate Rejection Decision
    rejected_req = approval_manager.reject_request(req_id, approver_id="admin-manager", reason="Tone is too casual")
    assert rejected_req.status == "rejected"
    assert rejected_req.rejection_reason == "Tone is too casual"
