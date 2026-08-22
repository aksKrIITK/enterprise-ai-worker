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


import os
import json
import logging

logger = logging.getLogger(__name__)


class MemoryStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MemoryStore, cls).__new__(cls)
            cls._instance.memories = []
            cls._instance.storage_file = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../../memory_store_data.json")
            )
            cls._instance._load_from_storage()
        return cls._instance

    def _load_from_storage(self):
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.memories = [MemoryItem(**item) for item in data]
                logger.info("Loaded %d memory items from persistent storage", len(self.memories))
        except Exception as err:
            logger.error("Failed to load memory store from file: %s", err)

    def _save_to_storage(self):
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump([mem.model_dump() for mem in self.memories], f, indent=2)
            logger.debug("Saved %d memories to persistent storage.", len(self.memories))
        except Exception as err:
            logger.error("Failed to save memory store to file: %s", err)

    def add_memory(self, memory: MemoryItem):
        self.memories.append(memory)
        self._save_to_storage()

    def clear(self):
        self.memories = []
        self._save_to_storage()

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
