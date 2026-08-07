from typing import Optional
import logging

from app.providers.base import BaseLLMProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.gemini_provider import GeminiProvider
from app.config import settings

# Set up module logger
logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """
    Factory for instantiating LLM provider implementations (OpenAI, Gemini).
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
            provider_name (Optional[str]): Target provider name ('openai', 'gemini').
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
            return OpenAIProvider(api_key=api_key, model=model)
        elif name == "gemini":
            return GeminiProvider(api_key=api_key, model=model)
        else:
            logger.error("Unsupported LLM provider requested: '%s'", provider_name)
            raise ValueError(f"Unsupported LLM provider: {provider_name}")

