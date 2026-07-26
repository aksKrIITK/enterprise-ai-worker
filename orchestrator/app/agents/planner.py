import uuid
from typing import List, Dict, Any
from app.agents.base_agent import BaseAgent
from app.graph.state import AgentInput, AgentOutput, SubTask
from app.providers.factory import LLMProviderFactory
from app.providers.base import LLMMessage


class PlannerAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "planner"

    async def run(self, input_data: AgentInput) -> AgentOutput:
        # Determine subtasks based on user instruction keyword analysis/LLM decomposition
        instruction_lower = input_data.instruction.lower()

        subtasks = []
        if any(w in instruction_lower for w in ["pr", "pull request", "github", "jira", "branch", "code", "issue", "ticket"]):
            subtasks.append(
                SubTask(
                    task_id=str(uuid.uuid4()),
                    agent_type="coding_agent",
                    instruction=input_data.instruction,
                )
            )
        elif any(w in instruction_lower for w in ["sql", "database", "table", "query", "count", "metrics", "select"]):
            subtasks.append(
                SubTask(
                    task_id=str(uuid.uuid4()),
                    agent_type="sql_agent",
                    instruction=input_data.instruction,
                )
            )

        elif any(w in instruction_lower for w in ["email", "gmail", "send to", "send an email"]):
            subtasks.append(
                SubTask(
                    task_id=str(uuid.uuid4()),
                    agent_type="email_agent",
                    instruction=input_data.instruction,
                )
            )

        elif any(w in instruction_lower for w in ["doc", "pdf", "file", "policy", "document", "what does", "find"]):
            subtasks.append(
                SubTask(
                    task_id=str(uuid.uuid4()),
                    agent_type="document_agent",
                    instruction=input_data.instruction,
                )
            )
        elif any(w in instruction_lower for w in ["research", "compare", "summary", "overview", "analyze"]):
            subtasks.append(
                SubTask(
                    task_id=str(uuid.uuid4()),
                    agent_type="researcher",
                    instruction=input_data.instruction,
                )
            )
        else:
            subtasks.append(
                SubTask(
                    task_id=str(uuid.uuid4()),
                    agent_type="document_agent",
                    instruction=input_data.instruction,
                )
            )


        return AgentOutput(
            task_id=input_data.task_id,
            status="success",
            result={"subtasks": [st.model_dump() for st in subtasks]},
            tokens_used=10,
        )

    async def synthesize_response(
        self,
        user_query: str,
        subtask_results: List[Dict[str, Any]],
        memories: List[str] = None,
    ) -> str:
        memories_text = "\n".join([f"- {m}" for m in (memories or [])])
        results_text = "\n\n".join(
            [f"[Subtask Result ({r.get('agent')}):]\n{r.get('output')}" for r in subtask_results]
        )

        messages = [
            LLMMessage(
                role="system",
                content="You are the Enterprise AI Planner. Synthesize a coherent, helpful, and professional answer from the completed agent subtask results. Incorporate durable memory facts if relevant.",
            ),
            LLMMessage(
                role="user",
                content=f"User Query: {user_query}\n\nKnown User Memory Context:\n{memories_text}\n\nSubtask Execution Outputs:\n{results_text}",
            ),
        ]

        llm_provider = LLMProviderFactory.get_provider()
        resp = await llm_provider.generate_response(messages)
        return resp.content
