import pytest
from app.memory.memory import MemoryService, MemoryStore

memory_store = MemoryStore()


@pytest.fixture(autouse=True)
def clear_memory_store():
    memory_store.clear()


def test_memory_consolidation_and_recall():
    service = MemoryService()

    messages = [
        "I always prefer concise answers",
        "I am the on-call lead for payment-service",
        "What is the weather today?",
    ]

    new_memories = service.consolidate_session_memory(
        tenant_id="tenant-1",
        user_id="user-100",
        user_messages=messages,
    )

    assert len(new_memories) == 2

    recalled = service.recall_memories("tenant-1", "user-100")
    assert len(recalled) == 2
    assert any("concise" in r for r in recalled)
    assert any("payment-service" in r for r in recalled)

    # Cross-tenant recall isolation check
    recalled_other_tenant = service.recall_memories("tenant-2", "user-100")
    assert len(recalled_other_tenant) == 0
