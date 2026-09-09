import asyncio
import random
import logging
from typing import List, Optional, AsyncGenerator
from app.providers.base import BaseLLMProvider, LLMMessage, LLMResponse
from app.exceptions import LLMProviderError

logger = logging.getLogger(__name__)


class ResilientLLMProvider(BaseLLMProvider):
    """
    Production-grade LLM provider wrapper implementing:
    1. Retry with exponential backoff & jitter for transient errors.
    2. Primary -> Secondary provider automatic failover.
    3. Streaming delta delegation with failover support.
    """

    def __init__(
        self,
        primary_provider: BaseLLMProvider,
        fallback_provider: Optional[BaseLLMProvider] = None,
        max_retries: int = 3,
        base_delay_sec: float = 0.5,
        max_delay_sec: float = 4.0,
    ):
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider
        self.max_retries = max_retries
        self.base_delay_sec = base_delay_sec
        self.max_delay_sec = max_delay_sec

    @property
    def provider_name(self) -> str:
        return self.primary_provider.provider_name

    @property
    def model_name(self) -> str:
        return self.primary_provider.model_name

    async def _execute_with_retry(
        self, provider: BaseLLMProvider, messages: List[LLMMessage], **kwargs
    ) -> LLMResponse:
        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return await provider.generate_response(messages, **kwargs)
            except Exception as err:
                last_exception = err
                if attempt == self.max_retries:
                    logger.warning(
                        "Provider %s attempt %d/%d failed: %s",
                        provider.provider_name,
                        attempt,
                        self.max_retries,
                        err,
                    )
                    break

                delay = min(self.max_delay_sec, self.base_delay_sec * (2 ** (attempt - 1)))
                jitter = random.uniform(0, 0.1 * delay)
                total_wait = delay + jitter
                logger.info(
                    "Retrying %s (attempt %d/%d) in %.2fs due to: %s",
                    provider.provider_name,
                    attempt + 1,
                    self.max_retries,
                    total_wait,
                    err,
                )
                await asyncio.sleep(total_wait)

        raise LLMProviderError(
            message=f"Provider {provider.provider_name} failed after {self.max_retries} retries: {last_exception}",
            provider=provider.provider_name,
            model=provider.model_name,
        )

    async def generate_response(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[dict]] = None,
    ) -> LLMResponse:
        try:
            return await self._execute_with_retry(
                self.primary_provider,
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
            )
        except LLMProviderError as primary_err:
            if not self.fallback_provider:
                raise primary_err

            logger.warning(
                "Primary provider %s failed. Triggering resilient failover to secondary provider %s...",
                self.primary_provider.provider_name,
                self.fallback_provider.provider_name,
            )
            try:
                fallback_resp = await self._execute_with_retry(
                    self.fallback_provider,
                    messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                )
                logger.info("Resilient failover to %s succeeded!", self.fallback_provider.provider_name)
                return fallback_resp
            except Exception as fallback_err:
                logger.error("Both primary and secondary LLM providers failed: %s", fallback_err)
                raise LLMProviderError(
                    message=f"Both primary ({self.primary_provider.provider_name}) and fallback ({self.fallback_provider.provider_name}) providers failed.",
                    provider="RESILIENT_FAILOVER_FAILED",
                    model=self.primary_provider.model_name,
                )

    async def stream_response(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        try:
            async for chunk in self.primary_provider.stream_response(
                messages, temperature=temperature, max_tokens=max_tokens
            ):
                yield chunk
        except Exception as primary_err:
            if self.fallback_provider:
                logger.warning(
                    "Primary provider streaming failed (%s). Falling back to secondary provider %s...",
                    primary_err,
                    self.fallback_provider.provider_name,
                )
                async for chunk in self.fallback_provider.stream_response(
                    messages, temperature=temperature, max_tokens=max_tokens
                ):
                    yield chunk
            else:
                raise primary_err
