import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from openai import AuthenticationError

from app.exceptions import InvalidApiKeyError
from app.main import app
from app.providers.openai_provider import OpenAIProvider

client = TestClient(app, raise_server_exceptions=False)


def run(coro):
    return asyncio.run(coro)


def openai_factory(seen):
    def factory(api_key, base_url=None):
        mock = AsyncMock()
        mock.close = AsyncMock()
        message = MagicMock(content=f"text-for-{api_key}")
        choice = MagicMock(message=message)
        mock.chat.completions.create = AsyncMock(return_value=MagicMock(choices=[choice]))
        seen[api_key] = mock
        return mock

    return factory


def test_parallel_keys_are_isolated():
    seen = {}

    async def main():
        provider = OpenAIProvider()
        calls = [
            provider.generate_text(
                system_prompt="sys",
                user_content="user",
                api_key=f"sk-user-{i}",
                response_schema={"type": "object"},
            )
            for i in range(8)
        ]
        return await asyncio.gather(*calls)

    with patch("app.providers.openai_provider.AsyncOpenAI", side_effect=openai_factory(seen)):
        texts = run(main())
    assert len(seen) == 8
    for i in range(8):
        assert texts[i] == f"text-for-sk-user-{i}"
        seen[f"sk-user-{i}"].chat.completions.create.assert_awaited_once()


def test_key_never_in_validation_response():
    secret = "x" * 501
    payload = {
        "provider": "openai",
        "api_key": secret,
        "product": {"name": "Манометр"},
    }
    response = client.post("/api/v1/generate", json=payload)
    assert response.status_code == 422
    assert secret not in response.text


def test_auth_error_response_has_no_key():
    secret = "sk-auth-secret-abcdef"

    async def boom(payload):
        raise InvalidApiKeyError("Неверный API-ключ OpenAI")

    payload = {
        "provider": "openai",
        "api_key": secret,
        "product": {"name": "Манометр"},
    }
    with patch("app.main.generate_card", side_effect=boom):
        response = client.post("/api/v1/generate", json=payload)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "invalid_api_key"
    assert secret not in response.text


def test_provider_auth_error_carries_no_key():
    secret = "sk-provider-secret-12345"
    failing = AsyncMock()
    failing.close = AsyncMock()
    response = MagicMock(status_code=401)
    failing.chat.completions.create = AsyncMock(
        side_effect=AuthenticationError("bad key", response=response, body=None)
    )
    with patch("app.providers.openai_provider.AsyncOpenAI", return_value=failing):
        try:
            run(
                OpenAIProvider().generate_text(
                    system_prompt="sys",
                    user_content="user",
                    api_key=secret,
                    response_schema={"type": "object"},
                )
            )
            raise AssertionError("expected InvalidApiKeyError")
        except InvalidApiKeyError as exc:
            assert secret not in str(exc)
