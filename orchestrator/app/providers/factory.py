from typing import Optional
from app.providers.base import BaseLLMProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.gemini_provider import GeminiProvider
from app.config import settings


class LLMProviderFactory:
    @staticmethod
    def get_provider(
        provider_name: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> BaseLLMProvider:
        name = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()

        if name == "openai":
            return OpenAIProvider(api_key=api_key, model=model)
        elif name == "gemini":
            return GeminiProvider(api_key=api_key, model=model)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
