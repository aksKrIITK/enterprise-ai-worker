import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.logging_context import RequestContext

logger = logging.getLogger(__name__)


class TraceAndLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that manages distributed trace propagation and logs HTTP metrics.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        trace_id = request.headers.get("X-Trace-Id") or f"trace-{uuid.uuid4()}"
        tenant_id = request.headers.get("X-Tenant-Id")
        user_id = request.headers.get("X-User-Id")

        RequestContext.set_context(trace_id=trace_id, tenant_id=tenant_id, user_id=user_id)
        request.state.trace_id = trace_id

        start_time = time.time()
        logger.info(
            "HTTP Request Started: %s %s | Tenant: %s | User: %s",
            request.method,
            request.url.path,
            tenant_id or "anonymous",
            user_id or "anonymous",
        )

        try:
            response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)

            response.headers["X-Trace-Id"] = trace_id
            logger.info(
                "HTTP Request Completed: %s %s [%s] in %sms",
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )
            return response
        except Exception as err:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                "HTTP Request Failed: %s %s in %sms | Error: %s",
                request.method,
                request.url.path,
                duration_ms,
                err,
                exc_info=True,
            )
            raise err
        finally:
            RequestContext.clear()
