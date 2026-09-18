import pytest
from app.providers.groq_provider import GroqProvider
from app.providers.factory import LLMProviderFactory
from app.providers.base import LLMMessage


@pytest.mark.asyncio
async def test_groq_provider_mock_generation():
    provider = GroqProvider()
    assert provider.provider_name == "groq"
    assert "llama" in provider.model_name.lower()

    messages = [LLMMessage(role="user", content="Test ultra-fast Groq response")]
    response = await provider.generate_response(messages)

    assert response.content is not None
    assert response.provider == "groq-mock"
    assert "Groq" in response.content


@pytest.mark.asyncio
async def test_groq_provider_streaming():
    provider = GroqProvider()
    messages = [LLMMessage(role="user", content="Stream Groq tokens")]
    tokens = []
    async for chunk in provider.stream_response(messages):
        tokens.append(chunk)

    assert len(tokens) > 0
    full_text = "".join(tokens)
    assert "Groq" in full_text


def test_factory_instantiates_groq():
    provider = LLMProviderFactory.get_provider(provider_name="groq")
    assert provider.provider_name == "groq"
