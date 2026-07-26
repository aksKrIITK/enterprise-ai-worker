from typing import List, Dict, Any, Optional
from app.rag.ingestion import DocumentChunk, DocumentIngestionService
from app.graph.state import Citation


class VectorStore:
    """In-memory & DB vector store abstraction with strict tenant isolation and ACL filtering."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance.chunks = []
        return cls._instance

    def add_chunks(self, chunks: List[DocumentChunk]):
        self.chunks.extend(chunks)

    def clear(self):
        self.chunks = []

    def cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = sum(a * a for a in vec_a) ** 0.5
        norm_b = sum(b * b for b in vec_b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def search(
        self,
        tenant_id: str,
        user_acls: List[str],
        query_embedding: List[float],
        user_role: str = "MEMBER",
        top_k: int = 4,
    ) -> List[DocumentChunk]:
        results = []

        for chunk in self.chunks:
            # 1. Strict Tenant Isolation Check
            if chunk.tenant_id != tenant_id:
                continue

            # 2. ACL Security Check
            if chunk.acl and user_role not in ["OWNER", "ADMIN"]:
                # User must possess at least one matching ACL tag
                has_acl_access = any(acl_item in user_acls for acl_item in chunk.acl)
                if not has_acl_access:
                    continue

            score = self.cosine_similarity(query_embedding, chunk.embedding)
            results.append((score, chunk))

        # Sort by similarity score descending
        results.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in results[:top_k]]


class ACLAwareRetriever:
    def __init__(self):
        self.ingestion_service = DocumentIngestionService()
        self.store = VectorStore()

    def search_documents(
        self,
        tenant_id: str,
        user_acls: List[str],
        query: str,
        user_role: str = "MEMBER",
        top_k: int = 4,
    ) -> tuple[List[DocumentChunk], List[Citation]]:
        query_vec = self.ingestion_service.generate_embedding(query)
        matching_chunks = self.store.search(
            tenant_id=tenant_id,
            user_acls=user_acls,
            query_embedding=query_vec,
            user_role=user_role,
            top_k=top_k,
        )

        citations = []
        for chunk in matching_chunks:
            citations.append(
                Citation(
                    document_id=chunk.document_id,
                    chunk_id=chunk.id,
                    source_type=chunk.metadata.get("source_type", "doc"),
                    title=chunk.metadata.get("title", "Untitled Document"),
                    snippet=chunk.content[:150] + "..." if len(chunk.content) > 150 else chunk.content,
                )
            )

        return matching_chunks, citations
