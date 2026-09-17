import pytest
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.exceptions import (
    AppException,
    ValidationError,
    GuardrailViolationError,
    AuthenticationError,
    TenantIsolationError,
)
from app.error_handlers import register_exception_handlers
from app.providers.resiliency import ResilientLLMProvider
from app.providers.base import BaseLLMProvider, LLMMessage, LLMResponse


app = FastAPI()
register_exception_handlers(app)


@app.get("/test-validation")
async def trigger_val_err():
    raise ValidationError("Invalid input payload")


@app.get("/test-auth")
async def trigger_auth_err():
    raise AuthenticationError("Token expired")


@app.get("/test-guardrail")
async def trigger_guardrail_err():
    raise GuardrailViolationError(
        message="Injection blocked",
        guardrail_name="PromptInjectionGuardrail",
        violations=["Pattern match"],
    )


client = TestClient(app)


def test_rfc7807_error_responses():
    r1 = client.get("/test-validation")
    assert r1.status_code == 400
    body1 = r1.json()
    assert body1["title"] == "VALIDATION_ERROR"
    assert "trace_id" in body1

    r2 = client.get("/test-auth")
    assert r2.status_code == 401
    body2 = r2.json()
    assert body2["title"] == "UNAUTHORIZED"

    r3 = client.get("/test-guardrail")
    assert r3.status_code == 422
    body3 = r3.json()
    assert body3["details"]["guardrail"] == "PromptInjectionGuardrail"


class FailingMockProvider(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "FailingMock"

    @property
    def model_name(self) -> str:
        return "mock-1"

    async def generate_response(self, messages, **kwargs):
        raise RuntimeError("API Connection Reset")

    async def stream_response(self, messages, **kwargs) -> AsyncGenerator[str, None]:
        raise RuntimeError("API Stream Reset")
        yield ""  # pragma: no cover


class SuccessfulMockProvider(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "SuccessfulMock"

    @property
    def model_name(self) -> str:
        return "mock-2"

    async def generate_response(self, messages, **kwargs):
        return LLMResponse(content="Fallback Success", tokens_used=10, provider="SuccessfulMock", model="mock-2")

    async def stream_response(self, messages, **kwargs) -> AsyncGenerator[str, None]:
        yield "Fallback Success"


@pytest.mark.asyncio
async def test_resilient_provider_failover():
    primary = FailingMockProvider()
    fallback = SuccessfulMockProvider()
    resilient_p = ResilientLLMProvider(
        primary_provider=primary,
        fallback_provider=fallback,
        max_retries=2,
        base_delay_sec=0.01,
    )

    resp = await resilient_p.generate_response([LLMMessage(role="user", content="Hello")])
    assert resp.content == "Fallback Success"
    assert resp.provider == "SuccessfulMock"
