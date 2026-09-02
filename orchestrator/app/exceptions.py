from typing import Optional, Dict, Any, List


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}


class ValidationError(AppException):
    """Raised when request payload or parameters fail validation."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class AuthenticationError(AppException):
    """Raised when service token or user authentication fails."""

    def __init__(self, message: str = "Invalid or missing authentication credentials."):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
        )


class TenantIsolationError(AppException):
    """Raised when tenant boundary enforcement fails."""

    def __init__(self, message: str = "Cross-tenant access prohibited."):
        super().__init__(
            message=message,
            status_code=403,
            error_code="TENANT_ACCESS_DENIED",
        )


class GuardrailViolationError(AppException):
    """Raised when input or output violates guardrail policies."""

    def __init__(
        self,
        message: str,
        guardrail_name: str,
        violations: List[str],
        details: Optional[Dict[str, Any]] = None,
    ):
        details = details or {}
        details.update({"guardrail": guardrail_name, "violations": violations})
        super().__init__(
            message=message,
            status_code=422,
            error_code="GUARDRAIL_VIOLATION",
            details=details,
        )
        self.guardrail_name = guardrail_name
        self.violations = violations


class LLMProviderError(AppException):
    """Raised when LLM completion fails after retry attempts."""

    def __init__(self, message: str, provider: str, model: str):
        super().__init__(
            message=message,
            status_code=502,
            error_code="LLM_PROVIDER_ERROR",
            details={"provider": provider, "model": model},
        )
        self.provider = provider
        self.model = model


class MCPToolExecutionError(AppException):
    """Raised when an external MCP tool execution fails."""

    def __init__(self, message: str, tool_name: str, server_name: str):
        super().__init__(
            message=message,
            status_code=500,
            error_code="MCP_TOOL_EXECUTION_ERROR",
            details={"tool_name": tool_name, "server_name": server_name},
        )
        self.tool_name = tool_name
        self.server_name = server_name


class ApprovalRequiredException(AppException):
    """Raised when a tool operation requires HITL approval."""

    def __init__(self, approval_id: str, action: str, details: Dict[str, Any]):
        super().__init__(
            message=f"Action '{action}' requires approval (ID: {approval_id})",
            status_code=202,
            error_code="APPROVAL_REQUIRED",
            details={"approval_id": approval_id, "action": action, "data": details},
        )
