from typing import Optional
import logging

from app.providers.base import BaseLLMProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider
from app.config import settings

# Set up module logger
logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """
    Factory for instantiating LLM provider implementations (OpenAI, Gemini, Groq).
    """

    @staticmethod
    def get_provider(
        provider_name: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> BaseLLMProvider:
        """
        Retrieves an LLM provider instance matching the given name or default configuration.
        
        Args:
            provider_name (Optional[str]): Target provider name ('openai', 'gemini', 'groq').
            api_key (Optional[str]): Optional API key override.
            model (Optional[str]): Optional model name override.
            
        Returns:
            BaseLLMProvider: Initialized LLM provider.
            
        Raises:
            ValueError: If the provider is unsupported.
        """
        name = (provider_name or settings.DEFAULT_LLM_PROVIDER).lower()
        logger.info("Instantiating LLM provider '%s' (model: %s)", name, model or "default")

        if name == "openai":
            primary = OpenAIProvider(api_key=api_key, model=model)
            fallback = GroqProvider() if getattr(settings, "GROQ_API_KEY", None) else (GeminiProvider() if settings.GEMINI_API_KEY else None)
        elif name == "gemini":
            primary = GeminiProvider(api_key=api_key, model=model)
            fallback = GroqProvider() if getattr(settings, "GROQ_API_KEY", None) else (OpenAIProvider() if settings.OPENAI_API_KEY else None)
        elif name == "groq":
            primary = GroqProvider(api_key=api_key, model=model)
            fallback = OpenAIProvider() if settings.OPENAI_API_KEY else (GeminiProvider() if settings.GEMINI_API_KEY else None)
        else:
            logger.error("Unsupported LLM provider requested: '%s'", provider_name)
            raise ValueError(f"Unsupported LLM provider: {provider_name}")

        from app.providers.resiliency import ResilientLLMProvider
        return ResilientLLMProvider(primary_provider=primary, fallback_provider=fallback)


