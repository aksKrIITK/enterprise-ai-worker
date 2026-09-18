import logging
import json
from app.logging_config import JSONFormatter
from app.logging_context import RequestContext


def test_json_formatter_structured_output():
    formatter = JSONFormatter()
    RequestContext.set_context(trace_id="test-trace-123", tenant_id="tenant-abc", user_id="user-xyz")

    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="User action processed",
        args=(),
        exc_info=None,
    )

    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["level"] == "INFO"
    assert parsed["message"] == "User action processed"
    assert parsed["trace_id"] == "test-trace-123"
    assert parsed["tenant_id"] == "tenant-abc"
    assert parsed["user_id"] == "user-xyz"

    RequestContext.clear()
