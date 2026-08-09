from typing import List, Dict, Any, Optional, Tuple
import logging

from app.rag.ingestion import DocumentChunk, DocumentIngestionService
from app.graph.state import Citation

# Set up module logger
logger = logging.getLogger(__name__)


class VectorStore:
    """In-memory & DB vector store abstraction with strict tenant isolation and ACL filtering."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            cls._instance.chunks = []
        return cls._instance

    def add_chunks(self, chunks: List[DocumentChunk]):
        """Appends new document chunks to the in-memory store."""
        if not chunks:
            return
        self.chunks.extend(chunks)
        logger.info("Added %d document chunks to VectorStore. Total chunks: %d", len(chunks), len(self.chunks))

    def clear(self):
        """Clears all stored document chunks."""
        count = len(self.chunks)
        self.chunks = []
        logger.info("Cleared VectorStore (removed %d chunks).", count)

    def cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """
        Computes cosine similarity between two vector embeddings.
        
        Returns 0.0 if vectors are empty or have zero norm.
        """
        try:
            if not vec_a or not vec_b:
                return 0.0
            dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
            norm_a = sum(a * a for a in vec_a) ** 0.5
            norm_b = sum(b * b for b in vec_b) ** 0.5
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return dot_product / (norm_a * norm_b)
        except Exception as err:
            logger.error("Error calculating cosine similarity: %s", err)
            return 0.0

    def search(
        self,
        tenant_id: str,
        user_acls: List[str],
        query_embedding: List[float],
        user_role: str = "MEMBER",
        top_k: int = 4,
    ) -> List[DocumentChunk]:
        """
        Performs similarity search over stored chunks subject to tenant isolation and ACL constraints.
        
        Args:
            tenant_id (str): Tenant context ID.
            user_acls (List[str]): ACL permission tags granted to caller.
            query_embedding (List[float]): Query vector.
            user_role (str): Role of the user (e.g. 'ADMIN', 'MEMBER').
            top_k (int): Maximum number of top matching chunks to return.
            
        Returns:
            List[DocumentChunk]: Filtered and ranked matching document chunks.
        """
        results = []
        tenant_skips = 0
        acl_skips = 0

        for chunk in self.chunks:
            # 1. Strict Tenant Isolation Check
            if chunk.tenant_id != tenant_id:
                tenant_skips += 1
                continue

            # 2. ACL Security Check
            if chunk.acl and user_role not in ["OWNER", "ADMIN"]:
                # User must possess at least one matching ACL tag
                has_acl_access = any(acl_item in user_acls for acl_item in chunk.acl)
                if not has_acl_access:
                    acl_skips += 1
                    continue

            score = self.cosine_similarity(query_embedding, chunk.embedding)
            results.append((score, chunk))

        logger.debug(
            "VectorStore search: examined %d chunks; tenant_skips=%d, acl_skips=%d, matches=%d",
            len(self.chunks), tenant_skips, acl_skips, len(results)
        )

        # Sort by similarity score descending
        results.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in results[:top_k]]


class ACLAwareRetriever:
    """
    Retriever wrapping ingestion embedding generation and ACL-aware VectorStore lookup.
    """

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
    ) -> Tuple[List[DocumentChunk], List[Citation]]:
        """
        Retrieves top-k document chunks for a query string and constructs citation references.
        """
        logger.info(
            "Searching documents for query='%s', tenant='%s', role='%s', top_k=%d",
            query[:50], tenant_id, user_role, top_k
        )

        try:
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

            logger.info("Found %d matching document chunks with citations.", len(matching_chunks))
            return matching_chunks, citations
        except Exception as err:
            logger.error("Error during document retrieval for query '%s': %s", query, err, exc_info=True)
            return [], []

