import pytest
from app.rag.ingestion import DocumentIngestionService
from app.rag.retriever import ACLAwareRetriever, VectorStore

ingestion_service = DocumentIngestionService()
retriever = ACLAwareRetriever()
store = VectorStore()


@pytest.fixture(autouse=True)
def clear_vector_store():
    store.clear()


def test_document_ingestion_and_chunking():
    content = "Enterprise AI Worker is a multi-tenant platform. " * 30
    chunks = ingestion_service.process_document(
        tenant_id="tenant-1",
        document_id="doc-1",
        title="Architecture Doc",
        content=content,
        source_type="pdf",
        acl=["role:ADMIN"],
    )
    assert len(chunks) > 1
    assert chunks[0].tenant_id == "tenant-1"
    assert chunks[0].acl == ["role:ADMIN"]
    assert len(chunks[0].embedding) == 1536


def test_tenant_isolation_in_vector_search():
    # Ingest document for Tenant 1
    chunks_t1 = ingestion_service.process_document(
        tenant_id="tenant-1",
        document_id="doc-t1",
        title="Tenant 1 Confidential",
        content="Secret financial data for Tenant 1",
        acl=[],
    )
    store.add_chunks(chunks_t1)

    # Ingest document for Tenant 2
    chunks_t2 = ingestion_service.process_document(
        tenant_id="tenant-2",
        document_id="doc-t2",
        title="Tenant 2 Confidential",
        content="Secret roadmap data for Tenant 2",
        acl=[],
    )
    store.add_chunks(chunks_t2)

    # User in Tenant 1 queries
    results_t1, _ = retriever.search_documents(
        tenant_id="tenant-1",
        user_acls=[],
        query="Secret data",
    )
    assert len(results_t1) > 0
    assert all(c.tenant_id == "tenant-1" for c in results_t1)

    # User in Tenant 2 queries
    results_t2, _ = retriever.search_documents(
        tenant_id="tenant-2",
        user_acls=[],
        query="Secret data",
    )
    assert len(results_t2) > 0
    assert all(c.tenant_id == "tenant-2" for c in results_t2)


def test_acl_filtering_enforcement():
    # Ingest Restricted Document with ACL ["group:execs"]
    restricted_chunks = ingestion_service.process_document(
        tenant_id="tenant-1",
        document_id="doc-restricted",
        title="Executive Compensation",
        content="Sensitive executive salary figures",
        acl=["group:execs"],
    )
    store.add_chunks(restricted_chunks)

    # User WITHOUT group:execs tag (MEMBER role)
    results_unauthorized, citations_unauth = retriever.search_documents(
        tenant_id="tenant-1",
        user_acls=["group:eng"],
        query="salary figures",
        user_role="MEMBER",
    )
    assert len(results_unauthorized) == 0

    # User WITH group:execs tag
    results_authorized, citations_auth = retriever.search_documents(
        tenant_id="tenant-1",
        user_acls=["group:execs"],
        query="salary figures",
        user_role="MEMBER",
    )
    assert len(results_authorized) > 0
    assert citations_auth[0].title == "Executive Compensation"

    # OWNER role bypasses ACL check
    results_owner, _ = retriever.search_documents(
        tenant_id="tenant-1",
        user_acls=[],
        query="salary figures",
        user_role="OWNER",
    )
    assert len(results_owner) > 0
