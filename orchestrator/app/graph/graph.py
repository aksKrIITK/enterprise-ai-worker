import uuid
from typing import Dict, Any, List, Generator
from app.graph.state import TaskGraphState, AgentInput
from app.agents.planner import PlannerAgent
from app.agents.document_agent import DocumentAgent
from app.agents.researcher import ResearcherAgent
from app.agents.email_agent import EmailAgent
from app.agents.sql_agent import SQLAgent
from app.agents.coding_agent import CodingAgent
from app.memory.memory import MemoryService


class MultiAgentGraph:
    def __init__(self):
        self.planner = PlannerAgent()
        self.doc_agent = DocumentAgent()
        self.researcher = ResearcherAgent()
        self.email_agent = EmailAgent()
        self.sql_agent = SQLAgent()
        self.coding_agent = CodingAgent()
        self.memory_service = MemoryService()




    async def execute(
        self,
        conversation_id: str,
        tenant_id: str,
        user_id: str,
        user_role: str,
        user_acls: List[str],
        user_instruction: str,
    ) -> Generator[Dict[str, Any], None, None]:
        """Execute the multi-agent execution pipeline and yield step-by-step event traces."""

        # Step 1: Recall Long-Term Memory
        memories = self.memory_service.recall_memories(tenant_id, user_id, user_instruction)

        yield {
            "event": "status",
            "data": {
                "status": "in_progress",
                "agent": "planner",
                "message": f"Planner decomposing request and recalling memory context ({len(memories)} facts recalled)...",
            },
        }

        # Step 2: Decompose via Planner Agent
        planner_input = AgentInput(
            task_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            user_role=user_role,
            user_acls=user_acls,
            instruction=user_instruction,
            conversation_id=conversation_id,
        )

        planner_output = await self.planner.run(planner_input)
        subtasks = planner_output.result.get("subtasks", [])

        subtask_results = []
        all_citations = []

        # Step 3: Execute Specialist Subtasks
        for subtask in subtasks:
            agent_type = subtask.get("agent_type")
            task_id = subtask.get("task_id")
            instruction = subtask.get("instruction")

            subtask_agent_input = AgentInput(
                task_id=task_id,
                tenant_id=tenant_id,
                user_id=user_id,
                user_role=user_role,
                user_acls=user_acls,
                instruction=instruction,
                conversation_id=conversation_id,
            )

            if agent_type == "coding_agent":
                yield {
                    "event": "status",
                    "data": {
                        "status": "in_progress",
                        "agent": "coding_agent",
                        "message": "Coding Agent executing dev task & checking approval gates...",
                    },
                }
                out = await self.coding_agent.run(subtask_agent_input)

                if out.status == "needs_approval":
                    yield {
                        "event": "needs_approval",
                        "data": {
                            "status": "paused",
                            "agent": "coding_agent",
                            "message": "Execution paused awaiting human approval for GitHub write operation.",
                            "approval_request": out.approval_request,
                        },
                    }
                    return

                subtask_results.append({"agent": "coding_agent", "output": out.result})

            elif agent_type == "sql_agent":

                yield {
                    "event": "status",
                    "data": {
                        "status": "in_progress",
                        "agent": "sql_agent",
                        "message": "SQL Agent generating, sandboxing, and executing read-only query...",
                    },
                }
                out = await self.sql_agent.run(subtask_agent_input)
                subtask_results.append(
                    {
                        "agent": "sql_agent",
                        "output": f"Generated SQL: `{out.result.get('generated_sql')}`\nRows returned: {out.result.get('row_count')}\nData: {out.result.get('data')}",
                    }
                )

            elif agent_type == "email_agent":

                yield {
                    "event": "status",
                    "data": {
                        "status": "in_progress",
                        "agent": "email_agent",
                        "message": "Email Agent processing request and checking approval gates...",
                    },
                }
                out = await self.email_agent.run(subtask_agent_input)

                if out.status == "needs_approval":
                    yield {
                        "event": "needs_approval",
                        "data": {
                            "status": "paused",
                            "agent": "email_agent",
                            "message": "Execution paused awaiting human approval.",
                            "approval_request": out.approval_request,
                        },
                    }
                    return

                subtask_results.append({"agent": "email_agent", "output": out.result})

            elif agent_type == "document_agent":
                yield {
                    "event": "status",
                    "data": {
                        "status": "in_progress",
                        "agent": "document_agent",
                        "message": "Document Agent executing ACL-aware vector search & chunk retrieval...",
                    },
                }
                out = await self.doc_agent.run(subtask_agent_input)
                subtask_results.append(
                    {"agent": "document_agent", "output": out.result.get("answer")}
                )
                all_citations.extend(out.citations)

            elif agent_type == "researcher":
                yield {
                    "event": "status",
                    "data": {
                        "status": "in_progress",
                        "agent": "researcher",
                        "message": "Researcher Agent analyzing documents and synthesizing findings...",
                    },
                }
                out = await self.researcher.run(subtask_agent_input)
                subtask_results.append(
                    {"agent": "researcher", "output": out.result.get("synthesis")}
                )
                all_citations.extend(out.citations)


        # Step 4: Final Synthesis by Planner
        yield {
            "event": "status",
            "data": {
                "status": "in_progress",
                "agent": "planner",
                "message": "Planner synthesizing final grounded response...",
            },
        }

        final_response = await self.planner.synthesize_response(
            user_query=user_instruction,
            subtask_results=subtask_results,
            memories=memories,
        )

        # Consolidate new memories post-session
        self.memory_service.consolidate_session_memory(tenant_id, user_id, [user_instruction])

        yield {
            "event": "result",
            "data": {
                "status": "completed",
                "final_response": final_response,
                "citations": [c.model_dump() for c in all_citations],
            },
        }
