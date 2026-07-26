from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.rag.ingestion import DocumentIngestionService
from app.rag.retriever import ACLAwareRetriever, VectorStore

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

ingestion_service = DocumentIngestionService()
retriever = ACLAwareRetriever()
store = VectorStore()


class IngestDocumentRequest(BaseModel):
    document_id: Optional[str] = None
    title: str
    content: str
    source_type: str = "pdf"
    acl: List[str] = []


class IngestDocumentResponse(BaseModel):
    document_id: str
    chunks_created: int
    status: str


class SearchDocumentRequest(BaseModel):
    query: str
    user_acls: List[str] = []
    user_role: str = "MEMBER"


@router.post("/ingest", response_model=IngestDocumentResponse)
async def ingest_document(
    request: IngestDocumentRequest,
    x_tenant_id: Optional[str] = Header("default-tenant"),
):
    chunks = ingestion_service.process_document(
        tenant_id=x_tenant_id,
        document_id=request.document_id,
        title=request.title,
        content=request.content,
        source_type=request.source_type,
        acl=request.acl,
    )
    store.add_chunks(chunks)

    return IngestDocumentResponse(
        document_id=chunks[0].document_id if chunks else "",
        chunks_created=len(chunks),
        status="success",
    )


@router.post("/search")
async def search_documents(
    request: SearchDocumentRequest,
    x_tenant_id: Optional[str] = Header("default-tenant"),
):
    chunks, citations = retriever.search_documents(
        tenant_id=x_tenant_id,
        user_acls=request.user_acls,
        query=request.query,
        user_role=request.user_role,
    )
    return {
        "results_count": len(chunks),
        "citations": [c.model_dump() for c in citations],
    }
