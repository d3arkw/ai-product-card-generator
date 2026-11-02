import asyncio

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
)
from openai import RateLimitError as OpenAIRateLimitError

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


class OpenAICompatibleProvider(BaseLLMProvider):
    name = "openai"
    label = "OpenAI"
    base_url_setting: str | None = None
    timeout_seconds: int | None = None

    def _timeout(self) -> int:
        return self.timeout_seconds or get_settings().request_timeout_seconds

    def _client(self, api_key: str) -> AsyncOpenAI:
        settings = get_settings()
        base_url = getattr(settings, self.base_url_setting) if self.base_url_setting else None
        return AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def generate_text(
        self,
        *,
        system_prompt: str,
        user_content: str,
        api_key: str,
        response_schema: dict,
        model_tier: str = "cheap",
    ) -> str:
        client = self._client(api_key)
        try:
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=self._resolve_model(model_tier),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "product_card",
                            "schema": response_schema,
                            "strict": False,
                        },
                    },
                ),
                timeout=self._timeout(),
            )
        except AuthenticationError as exc:
            raise InvalidApiKeyError(f"Неверный API-ключ {self.label}") from exc
        except OpenAIRateLimitError as exc:
            raise RateLimitError(f"Превышен лимит запросов {self.label}") from exc
        except (APITimeoutError, TimeoutError) as exc:
            raise UpstreamTimeoutError(f"{self.label} не ответил вовремя") from exc
        except APIConnectionError as exc:
            raise ServiceUnavailableError(f"{self.label} временно недоступен") from exc
        except APIStatusError as exc:
            raise self._map_status_error(exc) from exc
        finally:
            await client.close()
        message = response.choices[0].message if response.choices else None
        content = message.content if message is not None else None
        if not content:
            raise ServiceUnavailableError(f"{self.label} вернул пустой ответ")
        return content

    def _map_status_error(self, exc: APIStatusError) -> AppError:
        if exc.status_code == 401:
            return InvalidApiKeyError(f"Неверный API-ключ {self.label}")
        if exc.status_code == 429:
            return RateLimitError(f"Превышен лимит запросов {self.label}")
        if exc.status_code == 408:
            return UpstreamTimeoutError(f"{self.label} не ответил вовремя")
        if exc.status_code >= 500:
            return ServiceUnavailableError(f"{self.label} временно недоступен")
        return BadRequestError(f"{self.label} отклонил запрос ({exc.status_code}): {exc.message}")


class OpenAIProvider(OpenAICompatibleProvider):
    name = "openai"
    label = "OpenAI"
    model_setting = "openai_model"
