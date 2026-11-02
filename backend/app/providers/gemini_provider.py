import asyncio
import copy

from google import genai
from google.genai.errors import APIError as GeminiAPIError

from app.config import get_settings
from app.exceptions import (
    AppError,
    BadRequestError,
    InvalidApiKeyError,
    RateLimitError,
    ServiceUnavailableError,
    UpstreamTimeoutError,
)
from app.providers.base import BaseLLMProvider

_DROP_SCHEMA_KEYS = frozenset(
    {"$defs", "$schema", "additionalProperties", "minLength", "maxLength"}
)


def _gemini_schema(node: object, defs: dict) -> object:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            return _gemini_schema(copy.deepcopy(defs.get(ref.rsplit("/", 1)[-1], {})), defs)
        return {
            key: _gemini_schema(value, defs)
            for key, value in node.items()
            if key not in _DROP_SCHEMA_KEYS
        }
    if isinstance(node, list):
        return [_gemini_schema(value, defs) for value in node]
    return node


class GeminiProvider(BaseLLMProvider):
    name = "gemini"

    async def generate_text(
        self,
        *,
        system_prompt: str,
        user_content: str,
        api_key: str,
        response_schema: dict,
        model_tier: str = "cheap",
    ) -> str:
        client = genai.Client(api_key=api_key)
        try:
            try:
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=self._resolve_model(model_tier),
                        contents=user_content,
                        config={
                            "system_instruction": system_prompt,
                            "response_mime_type": "application/json",
                            "response_json_schema": _gemini_schema(
                                response_schema, response_schema.get("$defs", {})
                            ),
                        },
                    ),
                    timeout=get_settings().request_timeout_seconds,
                )
            except GeminiAPIError as exc:
                raise self._map_api_error(exc) from exc
            except TimeoutError as exc:
                raise UpstreamTimeoutError("Gemini не ответил вовремя") from exc
            if not response.text:
                raise ServiceUnavailableError("Gemini вернул пустой ответ")
            return response.text
        finally:
            client.close()

    @staticmethod
    def _map_api_error(exc: GeminiAPIError) -> AppError:
        try:
            code = int(exc.code)
        except (TypeError, ValueError):
            code = 0
        if code in (401, 403):
            return InvalidApiKeyError("Неверный API-ключ Gemini")
        if code == 429:
            return RateLimitError("Превышен лимит запросов Gemini")
        if code in (408, 504):
            return UpstreamTimeoutError("Gemini не ответил вовремя")
        if code >= 500 or code <= 0:
            return ServiceUnavailableError("Gemini временно недоступен")
        return BadRequestError(f"Gemini отклонил запрос ({code}): {exc.message}")
