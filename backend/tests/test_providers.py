import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.genai.errors import APIError as GeminiAPIError
from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError
from openai import RateLimitError as OpenAIRateLimitError

from app.deps import get_provider
from app.exceptions import (
    BadRequestError,
    InvalidApiKeyError,
    RateLimitError,
    ServiceUnavailableError,
    UpstreamTimeoutError,
)
from app.providers.gemini_provider import GeminiProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.routerai_provider import RouterAIProvider


def run(coro):
    return asyncio.run(coro)


def openai_client(content=None, error=None):
    client = AsyncMock()
    client.close = AsyncMock()
    if error is not None:
        client.chat.completions.create = AsyncMock(side_effect=error)
    else:
        message = MagicMock(content=content)
        choice = MagicMock(message=message)
        client.chat.completions.create = AsyncMock(return_value=MagicMock(choices=[choice]))
    return client


def gemini_client(text=None, error=None):
    models = AsyncMock()
    if error is not None:
        models.generate_content = AsyncMock(side_effect=error)
    else:
        models.generate_content = AsyncMock(return_value=MagicMock(text=text))
    client = MagicMock()
    client.aio.models = models
    return client, models


def call_openai(client):
    with patch("app.providers.openai_provider.AsyncOpenAI", return_value=client) as factory:
        text = run(
            OpenAIProvider().generate_text(
                system_prompt="sys",
                user_content="user",
                api_key="sk-x",
                response_schema={"type": "object"},
            )
        )
    return factory, text


def test_openai_success():
    client = openai_client(content='{"a": 1}')
    factory, text = call_openai(client)
    assert text == '{"a": 1}'
    factory.assert_called_once_with(api_key="sk-x", base_url=None)
    kwargs = client.chat.completions.create.await_args.kwargs
    assert kwargs["messages"][0] == {"role": "system", "content": "sys"}
    assert kwargs["messages"][1] == {"role": "user", "content": "user"}
    assert kwargs["response_format"]["type"] == "json_schema"
    client.close.assert_awaited_once()


def test_openai_auth_error():
    response = MagicMock(status_code=401)
    client = openai_client(error=AuthenticationError("bad key", response=response, body=None))
    with pytest.raises(InvalidApiKeyError):
        call_openai(client)
    client.close.assert_awaited_once()


def test_openai_rate_limit():
    response = MagicMock(status_code=429)
    client = openai_client(error=OpenAIRateLimitError("slow", response=response, body=None))
    with pytest.raises(RateLimitError):
        call_openai(client)


def test_openai_timeout():
    client = openai_client(error=TimeoutError())
    with pytest.raises(UpstreamTimeoutError):
        call_openai(client)


def test_openai_sdk_timeout():
    client = openai_client(error=APITimeoutError(request=MagicMock()))
    with pytest.raises(UpstreamTimeoutError):
        call_openai(client)


def test_openai_connection_error():
    client = openai_client(error=APIConnectionError(request=MagicMock()))
    with pytest.raises(ServiceUnavailableError):
        call_openai(client)


def test_openai_status_errors():
    server_error = MagicMock(status_code=500)
    client = openai_client(error=APIStatusError("fail", response=server_error, body=None))
    with pytest.raises(ServiceUnavailableError):
        call_openai(client)
    bad_request = MagicMock(status_code=400)
    client = openai_client(error=APIStatusError("bad", response=bad_request, body=None))
    with pytest.raises(BadRequestError):
        call_openai(client)


def test_openai_empty_response():
    client = openai_client(content="")
    with pytest.raises(ServiceUnavailableError):
        call_openai(client)


def call_gemini(client):
    with patch("app.providers.gemini_provider.genai.Client", return_value=client) as factory:
        text = run(
            GeminiProvider().generate_text(
                system_prompt="sys",
                user_content="user",
                api_key="sk-x",
                response_schema={"type": "object"},
            )
        )
    return factory, text


def test_gemini_success():
    client, models = gemini_client(text='{"a": 1}')
    factory, text = call_gemini(client)
    assert text == '{"a": 1}'
    factory.assert_called_once_with(api_key="sk-x")
    kwargs = models.generate_content.await_args.kwargs
    assert kwargs["contents"] == "user"
    assert kwargs["config"]["system_instruction"] == "sys"
    assert kwargs["config"]["response_mime_type"] == "application/json"


def test_gemini_unauthorized():
    client, _ = gemini_client(error=GeminiAPIError(401, {"error": {"message": "bad key"}}))
    with pytest.raises(InvalidApiKeyError):
        call_gemini(client)


def test_gemini_rate_limit():
    client, _ = gemini_client(error=GeminiAPIError(429, {"error": {"message": "slow"}}))
    with pytest.raises(RateLimitError):
        call_gemini(client)


def test_gemini_timeout():
    client, _ = gemini_client(error=TimeoutError())
    with pytest.raises(UpstreamTimeoutError):
        call_gemini(client)


def test_gemini_unavailable():
    client, _ = gemini_client(error=GeminiAPIError(503, {"error": {"message": "down"}}))
    with pytest.raises(ServiceUnavailableError):
        call_gemini(client)


def test_gemini_empty_response():
    client, _ = gemini_client(text="")
    with pytest.raises(ServiceUnavailableError):
        call_gemini(client)


def test_get_provider():
    assert isinstance(get_provider("openai"), OpenAIProvider)
    assert isinstance(get_provider("gemini"), GeminiProvider)
    assert isinstance(get_provider("routerai"), RouterAIProvider)
    with pytest.raises(BadRequestError):
        get_provider("anthropic")


def test_routerai_uses_base_url_and_model():
    client = openai_client(content='{"a": 1}')
    with patch("app.providers.openai_provider.AsyncOpenAI", return_value=client) as factory:
        text = run(
            RouterAIProvider().generate_text(
                system_prompt="sys",
                user_content="user",
                api_key="sk-r",
                response_schema={"type": "object"},
            )
        )
    assert text == '{"a": 1}'
    factory.assert_called_once_with(api_key="sk-r", base_url="https://routerai.ru/api/v1")
    kwargs = client.chat.completions.create.await_args.kwargs
    assert kwargs["model"] == "inclusionai/ling-3.0-flash"


def test_routerai_uses_extended_timeout():
    seen = {}

    async def spy(coro, timeout):
        seen["timeout"] = timeout
        return await coro

    client = openai_client(content='{"a": 1}')
    with (
        patch("app.providers.openai_provider.AsyncOpenAI", return_value=client),
        patch("app.providers.openai_provider.asyncio.wait_for", side_effect=spy),
    ):
        run(
            RouterAIProvider().generate_text(
                system_prompt="sys",
                user_content="user",
                api_key="sk-r",
                response_schema={"type": "object"},
            )
        )
    assert seen["timeout"] == 180


def test_routerai_auth_error():
    response = MagicMock(status_code=401)
    client = openai_client(error=AuthenticationError("bad", response=response, body=None))
    with (
        patch("app.providers.openai_provider.AsyncOpenAI", return_value=client),
        pytest.raises(InvalidApiKeyError),
    ):
        run(
            RouterAIProvider().generate_text(
                system_prompt="sys",
                user_content="user",
                api_key="sk-r",
                response_schema={"type": "object"},
            )
        )


def test_openai_not_found_is_bad_request():
    response = MagicMock(status_code=404)
    client = openai_client(error=APIStatusError("gone", response=response, body=None))
    with pytest.raises(BadRequestError):
        call_openai(client)


def test_openai_request_timeout_maps_to_upstream():
    response = MagicMock(status_code=408)
    client = openai_client(error=APIStatusError("slow", response=response, body=None))
    with pytest.raises(UpstreamTimeoutError):
        call_openai(client)


def test_openai_empty_choices():
    client = AsyncMock()
    client.close = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value=MagicMock(choices=[]))
    with pytest.raises(ServiceUnavailableError):
        call_openai(client)


def test_gemini_string_code_is_key_error():
    client, _ = gemini_client(error=GeminiAPIError("401", {"error": {"message": "bad"}}))
    with pytest.raises(InvalidApiKeyError):
        call_gemini(client)


def test_gemini_unknown_client_error_is_bad_request():
    client, _ = gemini_client(error=GeminiAPIError(409, {"error": {"message": "conflict"}}))
    with pytest.raises(BadRequestError):
        call_gemini(client)


def test_gemini_sends_sanitized_json_schema():
    schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "minLength": 1, "maxLength": 70},
            "item": {"$ref": "#/$defs/Item"},
        },
        "required": ["title"],
        "additionalProperties": False,
        "$defs": {
            "Item": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "additionalProperties": False,
            }
        },
    }
    client, models = gemini_client(text="{}")
    with patch("app.providers.gemini_provider.genai.Client", return_value=client):
        run(
            GeminiProvider().generate_text(
                system_prompt="sys",
                user_content="user",
                api_key="sk-x",
                response_schema=schema,
            )
        )
    sent = models.generate_content.await_args.kwargs["config"]["response_json_schema"]
    dumped = json.dumps(sent)
    assert "$ref" not in dumped
    assert "$defs" not in dumped
    assert "additionalProperties" not in dumped
    assert "minLength" not in dumped
    assert sent["properties"]["item"]["properties"]["name"] == {"type": "string"}


def test_gemini_client_is_closed():
    client, _ = gemini_client(text="{}")
    call_gemini(client)
    client.close.assert_called_once()
