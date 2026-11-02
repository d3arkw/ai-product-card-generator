import asyncio

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


class GeminiProvider(BaseLLMProvider):
    name = "gemini"

    async def generate_text(
        self,
        *,
        system_prompt: str,
        user_content: str,
        api_key: str,
        response_schema: dict,
    ) -> str:
        client = genai.Client(api_key=api_key)
        try:
            response = await asyncio.wait_for(
                client.aio.models.generate_content(
                    model=get_settings().gemini_model,
                    contents=user_content,
                    config={
                        "system_instruction": system_prompt,
                        "response_mime_type": "application/json",
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

    @staticmethod
    def _map_api_error(exc: GeminiAPIError) -> AppError:
        if exc.code in (401, 403):
            return InvalidApiKeyError("Неверный API-ключ Gemini")
        if exc.code == 429:
            return RateLimitError("Превышен лимит запросов Gemini")
        if exc.code == 504:
            return UpstreamTimeoutError("Gemini не ответил вовремя")
        if exc.code in (502, 503):
            return ServiceUnavailableError("Gemini временно недоступен")
        if exc.code == 400:
            return BadRequestError(f"Gemini отклонил запрос: {exc.message}")
        return AppError(f"Ошибка Gemini: {exc.message}")
