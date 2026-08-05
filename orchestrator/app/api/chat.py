from fastapi import APIRouter, Header, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio
import logging

# Module logger
logger = logging.getLogger(__name__)

from app.providers.base import LLMMessage
from app.providers.factory import LLMProviderFactory
from app.config import settings

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatRequest(BaseModel):
    """Payload model for chat and stream requests."""
    conversation_id: str
    messages: List[LLMMessage]
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7


class ChatResponse(BaseModel):
    """Response model for synchronous chat completion."""
    conversation_id: str
    response: str
    tokens_used: int
    provider: str
    model: str


def verify_service_token(x_service_token: Optional[str] = Header(None)) -> bool:
    """
    Validates inter-service communication secret token.
    
    In DEBUG mode, verification is bypassed. If a token header is provided, it must match the service secret.
    """
    if settings.DEBUG:
        logger.debug("Debug mode enabled: skipping service token check.")
        return True
    if x_service_token and x_service_token != settings.SERVICE_TO_SERVICE_SECRET:
        logger.warning("Service token verification failed for header: %s", x_service_token)
        raise HTTPException(status_code=401, detail="Invalid or missing service token.")
    return True



@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    x_tenant_id: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None),
    authenticated: bool = Depends(verify_service_token),
):
    """
    Synchronous Chat Endpoint.
    
    Dispatches prompt messages to the configured LLM provider and returns the complete text response.
    """
    logger.info(
        "Received sync chat request: conversation_id=%s, tenant=%s, user=%s, provider=%s",
        request.conversation_id, x_tenant_id, x_user_id, request.provider
    )
    
    try:
        provider = LLMProviderFactory.get_provider(
            provider_name=request.provider,
            model=request.model,
        )
        llm_resp = await provider.generate_response(
            messages=request.messages,
            temperature=request.temperature,
        )

        logger.info("Successfully generated response for conversation_id=%s", request.conversation_id)
        return ChatResponse(
            conversation_id=request.conversation_id,
            response=llm_resp.content,
            tokens_used=llm_resp.tokens_used,
            provider=llm_resp.provider,
            model=llm_resp.model,
        )
    except ValueError as ve:
        logger.error("Invalid provider configuration in chat endpoint: %s", ve)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as err:
        logger.error("Error processing chat request for conversation %s: %s", request.conversation_id, err, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal chat processing error: {err}")


@router.post("/stream")
async def stream_chat_endpoint(
    request: ChatRequest,
    x_tenant_id: Optional[str] = Header("default-tenant"),
    x_user_id: Optional[str] = Header("default-user"),
    x_user_role: Optional[str] = Header("MEMBER"),
    x_trace_id: Optional[str] = Header(None),
    authenticated: bool = Depends(verify_service_token),
):
    """
    Streaming Chat Endpoint (Server-Sent Events).
    
    Executes the MultiAgentGraph pipeline and streams status updates and message chunks back to the client.
    """
    from app.graph.graph import MultiAgentGraph
    from app.security.tracing import TracingContext
    from app.security.audit import AuditLogger

    logger.info(
        "Received stream chat request: conversation_id=%s, tenant=%s, user=%s, trace_id=%s",
        request.conversation_id, x_tenant_id, x_user_id, x_trace_id
    )

    try:
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
            try:
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
            except Exception as stream_err:
                logger.error("Error during SSE stream execution for conversation %s: %s", request.conversation_id, stream_err, exc_info=True)
                err_data = json.dumps({"error": str(stream_err), "trace_id": trace_id})
                yield f"event: error\ndata: {err_data}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as err:
        logger.error("Failed to initialize stream endpoint for conversation %s: %s", request.conversation_id, err, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to initiate stream: {err}")




