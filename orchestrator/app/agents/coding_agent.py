from app.agents.base_agent import BaseAgent
from app.graph.state import AgentInput, AgentOutput, ToolCallLog
from app.mcp.mcp_client import MCPClient
from app.approval.approval import ApprovalManager
from datetime import datetime, timezone


class CodingAgent(BaseAgent):
    def __init__(self):
        self.mcp_client = MCPClient()
        self.approval_manager = ApprovalManager()

    @property
    def name(self) -> str:
        return "coding_agent"

    async def run(self, input_data: AgentInput) -> AgentOutput:
        instruction_lower = input_data.instruction.lower()

        # Case 1: Write Action — Open Pull Request (Gated by Approval)
        if any(w in instruction_lower for w in ["pr", "pull request", "merge"]):


            repo = input_data.context.get("repo", "enterprise/app")
            pr_title = f"Feat: {input_data.instruction}"
            payload = {
                "repo": repo,
                "title": pr_title,
                "head": "feature/branch-1",
                "base": "main",
            }

            approval_req = self.approval_manager.create_approval_request(
                tenant_id=input_data.tenant_id,
                conversation_id=input_data.conversation_id,
                task_id=input_data.task_id,
                requested_action="github_open_pr",
                payload=payload,
                requested_by_agent=self.name,
                risk_level="high",
            )

            tool_log = ToolCallLog(
                tool_name="github_open_pr",
                input_params=payload,
                output_result={"approval_request_id": approval_req.id, "status": "pending_approval"},
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            return AgentOutput(
                task_id=input_data.task_id,
                status="needs_approval",
                result={
                    "message": "Pull Request drafted. Awaiting human approval before creating PR on GitHub.",
                    "pr_details": payload,
                },
                approval_request=approval_req.model_dump(),
                tokens_used=20,
                tool_calls=[tool_log],
            )

        # Case 2: Jira issue creation or inspection
        elif "jira" in instruction_lower or "ticket" in instruction_lower or "issue" in instruction_lower:
            jira_res = await self.mcp_client.execute_tool(
                "jira_create_issue",
                {"project": "DEV", "summary": input_data.instruction, "issue_type": "Task"},
            )
            tool_log = ToolCallLog(
                tool_name="jira_create_issue",
                input_params={"summary": input_data.instruction},
                output_result=jira_res,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            return AgentOutput(
                task_id=input_data.task_id,
                status="success",
                result={"jira_issue": jira_res},
                tokens_used=15,
                tool_calls=[tool_log],
            )

        # Case 3: Read repo files
        else:
            repo_res = await self.mcp_client.execute_tool(
                "github_read_repo",
                {"repo": "enterprise/app", "path": "src/"},
            )
            tool_log = ToolCallLog(
                tool_name="github_read_repo",
                input_params={"repo": "enterprise/app"},
                output_result=repo_res,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )

            return AgentOutput(
                task_id=input_data.task_id,
                status="success",
                result={"repository_files": repo_res.get("files", [])},
                tokens_used=15,
                tool_calls=[tool_log],
            )
