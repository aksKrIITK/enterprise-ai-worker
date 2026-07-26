from app.agents.base_agent import BaseAgent
from app.graph.state import AgentInput, AgentOutput, ToolCallLog
from app.mcp.mcp_client import MCPClient
from app.approval.approval import ApprovalManager
from app.providers.factory import LLMProviderFactory
from app.providers.base import LLMMessage
from datetime import datetime, timezone


class EmailAgent(BaseAgent):
    def __init__(self):
        self.mcp_client = MCPClient()
        self.approval_manager = ApprovalManager()

    @property
    def name(self) -> str:
        return "email_agent"

    async def run(self, input_data: AgentInput) -> AgentOutput:
        instruction_lower = input_data.instruction.lower()

        # Case 1: Send email request (requires approval)
        if "send" in instruction_lower or "email to" in instruction_lower:
            recipient = input_data.context.get("to", "client@acme.com")
            subject = input_data.context.get("subject", "Confirmation & Update")
            body = input_data.context.get("body", f"Hello,\n\nIn response to your request: {input_data.instruction}\n\nBest regards,\nEnterprise AI Worker")

            payload = {"to": recipient, "subject": subject, "body": body}

            # Create ApprovalRequest and pause execution
            approval_req = self.approval_manager.create_approval_request(
                tenant_id=input_data.tenant_id,
                conversation_id=input_data.conversation_id,
                task_id=input_data.task_id,
                requested_action="gmail_send_email",
                payload=payload,
                requested_by_agent=self.name,
                risk_level="high",
            )

            tool_log = ToolCallLog(
                tool_name="gmail_send_email",
                input_params=payload,
                output_result={"approval_request_id": approval_req.id, "status": "pending_approval"},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            return AgentOutput(
                task_id=input_data.task_id,
                status="needs_approval",
                result={
                    "message": "Email draft created. Awaiting human approval before sending.",
                    "draft": payload,
                },
                approval_request=approval_req.model_dump(),
                tokens_used=15,
                tool_calls=[tool_log],
            )

        # Case 2: Read / Draft email (auto-executed)
        else:
            inbox_res = await self.mcp_client.execute_tool("gmail_read_inbox", {"query": input_data.instruction})
            tool_log = ToolCallLog(
                tool_name="gmail_read_inbox",
                input_params={"query": input_data.instruction},
                output_result=inbox_res,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            return AgentOutput(
                task_id=input_data.task_id,
                status="success",
                result={"inbox": inbox_res.get("emails", [])},
                tokens_used=10,
                tool_calls=[tool_log],
            )
