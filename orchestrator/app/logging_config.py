import logging
import json
import sys
from datetime import datetime, timezone
from app.logging_context import RequestContext


class JSONFormatter(logging.Formatter):
    """
    Custom JSON Log Formatter outputting structured logs with correlated trace metadata.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": RequestContext.get_trace_id(),
            "tenant_id": RequestContext.get_tenant_id() or "system",
            "user_id": RequestContext.get_user_id() or "system",
            "filename": record.filename,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)

        return json.dumps(log_data)


def setup_logging(level: int = logging.INFO):
    """Initializes global structured JSON logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)

    # Quiet external library loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
