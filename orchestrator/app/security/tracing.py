import uuid
from typing import Optional


class TracingContext:
    """Distributed Tracing Context for propagating X-Trace-Id across gateway, orchestrator, and tools."""

    private_trace_id: Optional[str] = None

    @classmethod
    def get_or_create_trace_id(cls, incoming_trace_id: Optional[str] = None) -> str:
        if incoming_trace_id:
            cls.private_trace_id = incoming_trace_id
            return incoming_trace_id
        if not cls.private_trace_id:
            cls.private_trace_id = f"trace-{uuid.uuid4()}"
        return cls.private_trace_id

    @classmethod
    def clear(cls):
        cls.private_trace_id = None
