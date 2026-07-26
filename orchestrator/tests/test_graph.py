import pytest
from app.graph.graph import MultiAgentGraph
from app.rag.ingestion import DocumentIngestionService
from app.rag.retriever import VectorStore

ingestion_service = DocumentIngestionService()
store = VectorStore()


@pytest.mark.asyncio
async def test_multi_agent_graph_execution():
    store.clear()

    # Seed document
    doc_chunks = ingestion_service.process_document(
        tenant_id="tenant-alpha",
        document_id="doc-alpha-1",
        title="Enterprise Worker Security Policy",
        content="Enterprise AI Worker enforces strict RBAC and tenant isolation across all services.",
        acl=[],
    )
    store.add_chunks(doc_chunks)

    graph = MultiAgentGraph()
    events = []

    async for event in graph.execute(
        conversation_id="conv-graph-test",
        tenant_id="tenant-alpha",
        user_id="user-1",
        user_role="MEMBER",
        user_acls=[],
        user_instruction="What does the security policy say about tenant isolation?",
    ):
        events.append(event)

    assert len(events) >= 3
    event_types = [e["event"] for e in events]
    assert "status" in event_types
    assert "result" in event_types

    result_event = next(e for e in events if e["event"] == "result")
    assert result_event["data"]["status"] == "completed"
    assert "final_response" in result_event["data"]
