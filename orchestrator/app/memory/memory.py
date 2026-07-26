import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.rag.ingestion import DocumentIngestionService


class MemoryItem(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    memory_type: str  # "preference", "fact", "role"
    content: str
    embedding: List[float]
    importance: float = 1.0


class MemoryStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MemoryStore, cls).__new__(cls)
            cls._instance.memories = []
        return cls._instance

    def add_memory(self, memory: MemoryItem):
        self.memories.append(memory)

    def clear(self):
        self.memories = []

    def get_memories(self, tenant_id: str, user_id: str) -> List[MemoryItem]:
        return [
            m for m in self.memories
            if m.tenant_id == tenant_id and m.user_id == user_id
        ]


class MemoryService:
    def __init__(self):
        self.store = MemoryStore()
        self.ingestion_service = DocumentIngestionService()

    def consolidate_session_memory(
        self,
        tenant_id: str,
        user_id: str,
        user_messages: List[str],
    ) -> List[MemoryItem]:
        """Extract durable user facts and preferences from conversation messages."""
        new_memories = []
        for msg in user_messages:
            msg_lower = msg.lower()
            if any(kw in msg_lower for kw in ["prefer", "always", "lead for", "my role", "on-call", "team"]):
                memory_id = str(uuid.uuid4())
                vec = self.ingestion_service.generate_embedding(msg)

                mem = MemoryItem(
                    id=memory_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    memory_type="preference" if "prefer" in msg_lower else "fact",
                    content=msg,
                    embedding=vec,
                    importance=1.5 if "always" in msg_lower else 1.0,
                )
                self.store.add_memory(mem)
                new_memories.append(mem)
        return new_memories

    def recall_memories(
        self,
        tenant_id: str,
        user_id: str,
        query: str = "",
    ) -> List[str]:
        user_mems = self.store.get_memories(tenant_id, user_id)
        return [m.content for m in user_mems]
