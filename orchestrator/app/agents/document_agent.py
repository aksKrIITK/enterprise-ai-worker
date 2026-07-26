from app.agents.base_agent import BaseAgent
from app.graph.state import AgentInput, AgentOutput
from app.rag.retriever import ACLAwareRetriever
from app.providers.factory import LLMProviderFactory
from app.providers.base import LLMMessage


class DocumentAgent(BaseAgent):
    def __init__(self):
        self.retriever = ACLAwareRetriever()

    @property
    def name(self) -> str:
        return "document_agent"

    async def run(self, input_data: AgentInput) -> AgentOutput:
        # Retrieve ACL-filtered document chunks
        matching_chunks, citations = self.retriever.search_documents(
            tenant_id=input_data.tenant_id,
            user_acls=input_data.user_acls,
            query=input_data.instruction,
            user_role=input_data.user_role,
            top_k=4,
        )

        if not matching_chunks:
            return AgentOutput(
                task_id=input_data.task_id,
                status="success",
                result={
                    "answer": "No relevant internal documents found or you do not have permission to view them.",
                    "chunks_found": 0,
                },
                citations=[],
                tokens_used=10,
            )

        context_text = "\n\n".join(
            [f"[Document: {c.metadata.get('title', 'Doc')} (ID: {c.document_id})]:\n{c.content}" for c in matching_chunks]
        )

        prompt_messages = [
            LLMMessage(
                role="system",
                content="You are the Document Agent. Answer the user request strictly using the provided document context. Ground every statement and cite the document titles.",
            ),
            LLMMessage(
                role="user",
                content=f"Context:\n{context_text}\n\nInstruction: {input_data.instruction}",
            ),
        ]

        llm_provider = LLMProviderFactory.get_provider()
        llm_response = await llm_provider.generate_response(prompt_messages)

        return AgentOutput(
            task_id=input_data.task_id,
            status="success",
            result={"answer": llm_response.content, "chunks_found": len(matching_chunks)},
            citations=citations,
            tokens_used=llm_response.tokens_used,
        )
