from typing import AsyncGenerator, List, Optional
import os
import logging
from openai import AsyncOpenAI
from app.providers.base import BaseLLMProvider, LLMMessage, LLMResponse
from app.config import settings

# Module logger
logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI LLM Provider implementation with mock fallbacks for testing or missing credentials.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
        self.model = model or settings.OPENAI_MODEL
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
            logger.info("Initialized OpenAIProvider with configured API key and model '%s'.", self.model)
        else:
            self.client = None
            logger.info("Initialized OpenAIProvider in mock mode (no API key provided).")

    async def generate_response(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generates a chat response using OpenAI API, falling back to mock response on client missing or API failure.
        """
        if not self.client:
            logger.debug("Generating mock OpenAI response for message: %s", messages[-1].content if messages else "")
            return LLMResponse(
                content=f"[Mock OpenAI Response for Phase 0]: Handled '{messages[-1].content if messages else ''}'",
                tokens_used=15,
                provider="openai-mock",
                model=self.model,
            )

        try:
            formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
            logger.debug("Calling OpenAI API chat completions with model '%s'", self.model)
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0

            return LLMResponse(
                content=content,
                tokens_used=tokens_used,
                provider="openai",
                model=self.model,
            )
        except Exception as err:
            logger.warning("OpenAI API call failed (%s); falling back to mock response.", err)
            return LLMResponse(
                content=f"[Mock OpenAI Response for Phase 0]: Handled '{messages[-1].content if messages else ''}'",
                tokens_used=15,
                provider="openai-mock",
                model=self.model,
            )

    async def stream_response(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Streams chat completion tokens from OpenAI API, falling back to mock streaming on failure.
        """
        if not self.client:
            mock_tokens = [
                "[Mock OpenAI SSE Stream]: ",
                "Received your message ",
                f"'{messages[-1].content if messages else ''}'. ",
                "Enterprise AI Orchestrator Phase 0 is online!",
            ]
            for token in mock_tokens:
                yield token
            return

        try:
            formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=formatted_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as err:
            logger.warning("OpenAI streaming API call failed (%s); falling back to mock stream.", err)
            mock_tokens = [
                "[Mock OpenAI SSE Stream]: ",
                "Received your message ",
                f"'{messages[-1].content if messages else ''}'. ",
                "Enterprise AI Orchestrator Phase 0 is online!",
            ]
            for token in mock_tokens:
                yield token

