import uuid
from contextvars import ContextVar
from typing import Optional

trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id_var", default=None)
tenant_id_var: ContextVar[Optional[str]] = ContextVar("tenant_id_var", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id_var", default=None)


class RequestContext:
    """Async context manager and static accessor for request metadata across coroutines."""

    @staticmethod
    def get_trace_id() -> str:
        tid = trace_id_var.get()
        if not tid:
            tid = f"trace-{uuid.uuid4()}"
            trace_id_var.set(tid)
        return tid

    @staticmethod
    def set_context(trace_id: Optional[str] = None, tenant_id: Optional[str] = None, user_id: Optional[str] = None):
        if trace_id:
            trace_id_var.set(trace_id)
        if tenant_id:
            tenant_id_var.set(tenant_id)
        if user_id:
            user_id_var.set(user_id)

    @staticmethod
    def get_tenant_id() -> Optional[str]:
        return tenant_id_var.get()

    @staticmethod
    def get_user_id() -> Optional[str]:
        return user_id_var.get()

    @staticmethod
    def clear():
        trace_id_var.set(None)
        tenant_id_var.set(None)
        user_id_var.set(None)
