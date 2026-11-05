from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import settings


def chat_model(spec: str):
    provider, _, model = spec.partition(":")
    if provider == "cerebras":
        return OpenAIChatModel(model, provider=OpenAIProvider(base_url=settings.cerebras_base_url, api_key=settings.cerebras_api_key))
    if provider == "nvidia":
        return OpenAIChatModel(model, provider=OpenAIProvider(base_url=settings.nvidia_base_url, api_key=settings.nvidia_api_key))
    return spec
