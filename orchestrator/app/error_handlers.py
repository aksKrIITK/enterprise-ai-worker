from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone
import logging

from app.exceptions import AppException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Registers standard RFC 7807 problem details error handlers for FastAPI."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        trace_id = getattr(request.state, "trace_id", "unknown-trace")
        logger.warning(
            "Application error [%s] (%s): %s | Trace: %s",
            exc.error_code,
            exc.status_code,
            exc.message,
            trace_id,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "type": f"https://api.enterprise-ai.internal/errors/{exc.error_code.lower()}",
                "title": exc.error_code,
                "status": exc.status_code,
                "detail": exc.message,
                "instance": str(request.url.path),
                "trace_id": trace_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": exc.details,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        trace_id = getattr(request.state, "trace_id", "unknown-trace")
        errors = exc.errors()
        logger.warning("Request validation failed for %s: %s | Trace: %s", request.url.path, errors, trace_id)

        return JSONResponse(
            status_code=400,
            content={
                "type": "https://api.enterprise-ai.internal/errors/validation_error",
                "title": "VALIDATION_ERROR",
                "status": 400,
                "detail": "Invalid request payload format.",
                "instance": str(request.url.path),
                "trace_id": trace_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": {"errors": errors},
            },
        )

    @app.exception_handler(Exception)
    async def global_unhandled_exception_handler(request: Request, exc: Exception):
        trace_id = getattr(request.state, "trace_id", "unknown-trace")
        logger.error("Unhandled server exception at %s: %s | Trace: %s", request.url.path, exc, trace_id, exc_info=True)

        return JSONResponse(
            status_code=500,
            content={
                "type": "https://api.enterprise-ai.internal/errors/internal_server_error",
                "title": "INTERNAL_SERVER_ERROR",
                "status": 500,
                "detail": "An unexpected internal server error occurred.",
                "instance": str(request.url.path),
                "trace_id": trace_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "details": {},
            },
        )
