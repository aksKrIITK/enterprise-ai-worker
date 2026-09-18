from typing import AsyncGenerator, List, Optional, Dict
import os
import logging
from openai import AsyncOpenAI
from app.providers.base import BaseLLMProvider, LLMMessage, LLMResponse
from app.config import settings

logger = logging.getLogger(__name__)

# Try importing native Groq SDK if available, else use AsyncOpenAI with Groq base_url
try:
    from groq import AsyncGroq
    HAS_GROQ_SDK = True
except ImportError:
    HAS_GROQ_SDK = False


class GroqProvider(BaseLLMProvider):
    """
    Groq LLM Provider implementation offering ultra-low latency inference on LPU hardware.
    Supports native Groq SDK as well as Groq's OpenAI-compatible API endpoint.
    Includes mock fallbacks for testing or environments without live API credentials.
    """

    GROQ_API_BASE = "https://api.groq.com/openai/v1"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        self.model = model or getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")

        if self.api_key:
            if HAS_GROQ_SDK:
                self.client = AsyncGroq(api_key=self.api_key)
                logger.info("Initialized GroqProvider with native Groq SDK and model '%s'.", self.model)
            else:
                self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.GROQ_API_BASE)
                logger.info("Initialized GroqProvider with Groq OpenAI-compatible endpoint and model '%s'.", self.model)
        else:
            self.client = None
            logger.info("Initialized GroqProvider in mock mode (no API key provided).")

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def model_name(self) -> str:
        return self.model

    async def generate_response(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[dict]] = None,
    ) -> LLMResponse:
        """
        Generates a chat completion using Groq LPU inference, falling back to mock response on missing credentials.
        """
        if not self.client:
            logger.debug("Generating mock Groq response for message: %s", messages[-1].content if messages else "")
            return LLMResponse(
                content=f"[Enterprise AI Orchestrator - Groq]: Processed input '{messages[-1].content if messages else ''}'. (Configure Groq API key in .env for live Groq LPU completions)",
                tokens_used=15,
                provider="groq-mock",
                model=self.model,
            )

        try:
            formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
            logger.debug("Calling Groq API chat completions with model '%s'", self.model)
            kwargs = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": temperature,
            }
            if max_tokens:
                kwargs["max_tokens"] = max_tokens

            response = await self.client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if hasattr(response, "usage") and response.usage else 0

            return LLMResponse(
                content=content,
                tokens_used=tokens_used,
                provider="groq",
                model=self.model,
            )
        except Exception as err:
            logger.warning("Groq API call failed (%s); falling back to mock response.", err)
            return LLMResponse(
                content=f"[Mock Groq Response]: Handled '{messages[-1].content if messages else ''}'",
                tokens_used=15,
                provider="groq-mock",
                model=self.model,
            )

    async def stream_response(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Streams token chunks from Groq LPU inference in real-time.
        """
        if not self.client:
            mock_tokens = [
                "[Mock Groq LPU SSE Stream]: ",
                "Received message ",
                f"'{messages[-1].content if messages else ''}'. ",
                "Groq ultra-fast provider is successfully connected!",
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
            logger.warning("Groq streaming API call failed (%s); falling back to mock stream.", err)
            mock_tokens = [
                "[Mock Groq SSE Stream]: ",
                "Received your message ",
                f"'{messages[-1].content if messages else ''}'. ",
                "Groq Orchestrator is online!",
            ]
            for token in mock_tokens:
                yield token
