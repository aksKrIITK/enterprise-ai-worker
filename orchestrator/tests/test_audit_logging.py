import pytest
from app.security.audit import AuditLogger
from app.security.tracing import TracingContext

audit_logger = AuditLogger()


@pytest.fixture(autouse=True)
def clear_audit_records():
    audit_logger.clear()
    TracingContext.clear()


def test_audit_logging_and_tracing_propagation():
    trace_id = TracingContext.get_or_create_trace_id("test-trace-12345")
    assert trace_id == "test-trace-12345"

    record = audit_logger.log(
        tenant_id="tenant-alpha",
        actor_id="user-100",
        action="TOOL_CALL_EXECUTED",
        resource_type="MCP_TOOL",
        resource_id="gmail_send_email",
        trace_id=trace_id,
        details={"recipient": "client@acme.com"},
    )

    assert record.tenant_id == "tenant-alpha"
    assert record.actor_id == "user-100"
    assert record.action == "TOOL_CALL_EXECUTED"
    assert record.trace_id == "test-trace-12345"

    logs = audit_logger.get_tenant_audit_logs("tenant-alpha")
    assert len(logs) == 1
    assert logs[0].id == record.id

    # Verify tenant isolation of audit logs
    other_tenant_logs = audit_logger.get_tenant_audit_logs("tenant-beta")
    assert len(other_tenant_logs) == 0
