from typing import AsyncGenerator, List, Optional
import os
from app.providers.base import BaseLLMProvider, LLMMessage, LLMResponse
from app.config import settings

try:
    from google import genai
    from google.genai import types
    HAS_GEMINI_SDK = True
except ImportError:
    HAS_GEMINI_SDK = False


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
        self.model = model or settings.GEMINI_MODEL
        if self.api_key and HAS_GEMINI_SDK:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    async def generate_response(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        if not self.client:
            return LLMResponse(
                content=f"[Mock Gemini Response for Phase 0]: Handled '{messages[-1].content}'",
                tokens_used=15,
                provider="gemini-mock",
                model=self.model,
            )

        prompt = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )

        return LLMResponse(
            content=response.text or "",
            tokens_used=20,
            provider="gemini",
            model=self.model,
        )

    async def stream_response(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        if not self.client:
            mock_tokens = [
                "[Mock Gemini SSE Stream]: ",
                "Received message ",
                f"'{messages[-1].content}'. ",
                "Gemini provider is successfully connected!",
            ]
            for token in mock_tokens:
                yield token
            return

        prompt = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])
        response_stream = self.client.models.generate_content_stream(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
        )

        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
