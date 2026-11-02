from app.exceptions import BadRequestError
from app.providers.base import BaseLLMProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.routerai_provider import RouterAIProvider

_providers: dict[str, BaseLLMProvider] = {
    "openai": OpenAIProvider(),
    "gemini": GeminiProvider(),
    "routerai": RouterAIProvider(),
}


def get_provider(name: str) -> BaseLLMProvider:
    try:
        return _providers[name]
    except KeyError as exc:
        raise BadRequestError(f"Неизвестный провайдер: {name}") from exc
