import hashlib
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class DocumentChunk(BaseModel):
    id: str
    document_id: str
    tenant_id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    acl: List[str]


class DocumentIngestionService:
    def __init__(self, embedding_dim: int = 1536):
        self.embedding_dim = embedding_dim

    def generate_embedding(self, text: str) -> List[float]:
        """Generate a deterministic 1536-dim normalized vector representation for testing/RAG fallback."""
        hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        vector = []
        for i in range(self.embedding_dim):
            byte_val = hash_bytes[i % len(hash_bytes)]
            val = (byte_val / 255.0) * 2.0 - 1.0
            vector.append(val)
        # Normalize
        norm = sum(x * x for x in vector) ** 0.5
        if norm > 0:
            vector = [x / norm for x in vector]
        return vector

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            if end == len(text):
                break
            start += chunk_size - overlap
        return chunks

    def process_document(
        self,
        tenant_id: str,
        document_id: Optional[str],
        title: str,
        content: str,
        source_type: str = "pdf",
        acl: Optional[List[str]] = None,
    ) -> List[DocumentChunk]:
        doc_id = document_id or str(uuid.uuid4())
        acl_list = acl or []
        chunks_text = self.chunk_text(content)

        document_chunks = []
        for idx, chunk_str in enumerate(chunks_text):
            chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_id}-{idx}"))
            embedding = self.generate_embedding(chunk_str)

            document_chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    document_id=doc_id,
                    tenant_id=tenant_id,
                    content=chunk_str,
                    embedding=embedding,
                    metadata={
                        "title": title,
                        "chunk_index": idx,
                        "source_type": source_type,
                    },
                    acl=acl_list,
                )
            )

        return document_chunks
