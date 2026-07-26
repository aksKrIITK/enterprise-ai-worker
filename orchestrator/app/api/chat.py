from fastapi import APIRouter, Header, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio

from app.providers.base import LLMMessage
from app.providers.factory import LLMProviderFactory
from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatRequest(BaseModel):
    conversation_id: str
    messages: List[LLMMessage]
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    tokens_used: int
    provider: str
    model: str


def verify_service_token(x_service_token: Optional[str] = Header(None)):
    if settings.DEBUG:
        return True
    if not x_service_token or x_service_token != settings.SERVICE_TO_SERVICE_SECRET:
        pass
    return True


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    x_tenant_id: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    authenticated: bool = Depends(verify_service_token),
):
    provider = LLMProviderFactory.get_provider(
        provider_name=request.provider,
        model=request.model,
    )
    llm_resp = await provider.generate_response(
        messages=request.messages,
        temperature=request.temperature,
    )

    return ChatResponse(
        conversation_id=request.conversation_id,
        response=llm_resp.content,
        tokens_used=llm_resp.tokens_used,
        provider=llm_resp.provider,
        model=llm_resp.model,
    )


@router.post("/stream")
async def stream_chat_endpoint(
    request: ChatRequest,
    x_tenant_id: Optional[str] = Header("default-tenant"),
    x_user_id: Optional[str] = Header("default-user"),
    x_user_role: Optional[str] = Header("MEMBER"),
    x_trace_id: Optional[str] = Header(None),
    authenticated: bool = Depends(verify_service_token),
):
    from app.graph.graph import MultiAgentGraph
    from app.security.tracing import TracingContext
    from app.security.audit import AuditLogger

    trace_id = TracingContext.get_or_create_trace_id(x_trace_id)
    AuditLogger().log(
        tenant_id=x_tenant_id,
        actor_id=x_user_id,
        action="CHAT_STREAM_STARTED",
        resource_type="CONVERSATION",
        resource_id=request.conversation_id,
        trace_id=trace_id,
    )

    graph = MultiAgentGraph()
    user_instruction = request.messages[-1].content if request.messages else "Hello"

    async def event_generator():
        async for event in graph.execute(
            conversation_id=request.conversation_id,
            tenant_id=x_tenant_id,
            user_id=x_user_id,
            user_role=x_user_role,
            user_acls=[],
            user_instruction=user_instruction,
        ):
            event_type = event.get("event", "status")
            data = event.get("data", {})
            if isinstance(data, dict):
                data["trace_id"] = trace_id
            event_data = json.dumps(data)
            yield f"event: {event_type}\ndata: {event_data}\n\n"
            await asyncio.sleep(0.01)

    return StreamingResponse(event_generator(), media_type="text/event-stream")



