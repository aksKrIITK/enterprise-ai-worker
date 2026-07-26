from app.agents.base_agent import BaseAgent
from app.graph.state import AgentInput, AgentOutput
from app.rag.retriever import ACLAwareRetriever
from app.graph_engine.knowledge_graph import KnowledgeGraphEngine
from app.providers.factory import LLMProviderFactory
from app.providers.base import LLMMessage


class ResearcherAgent(BaseAgent):
    def __init__(self):
        self.retriever = ACLAwareRetriever()
        self.kg_engine = KnowledgeGraphEngine()

    @property
    def name(self) -> str:
        return "researcher"

    async def run(self, input_data: AgentInput) -> AgentOutput:
        # 1. Vector Search
        matching_chunks, citations = self.retriever.search_documents(
            tenant_id=input_data.tenant_id,
            user_acls=input_data.user_acls,
            query=input_data.instruction,
            user_role=input_data.user_role,
            top_k=5,
        )

        doc_snippets = "\n".join(
            [f"- [{c.metadata.get('title')}]: {c.content[:200]}" for c in matching_chunks]
        ) if matching_chunks else "No internal document hits."

        # 2. Knowledge Graph Traversal
        kg_nodes = self.kg_engine.multi_hop_search(
            start_entity_name=input_data.instruction,
            target_relation_chain=["OWNS"],
        )
        kg_context = "\n".join([f"- Related Entity: {n.name} ({n.type})" for n in kg_nodes]) if kg_nodes else "No graph hits."

        messages = [
            LLMMessage(
                role="system",
                content="You are the Researcher Agent. Synthesize information from hybrid retrieval (vector similarity + Knowledge Graph multi-hop relationships).",
            ),
            LLMMessage(
                role="user",
                content=f"Instruction: {input_data.instruction}\nDocument Knowledge:\n{doc_snippets}\nKnowledge Graph Relationships:\n{kg_context}",
            ),
        ]

        llm_provider = LLMProviderFactory.get_provider()
        llm_resp = await llm_provider.generate_response(messages)

        return AgentOutput(
            task_id=input_data.task_id,
            status="success",
            result={"synthesis": llm_resp.content, "sources_count": len(citations)},
            citations=citations,
            tokens_used=llm_resp.tokens_used,
        )

