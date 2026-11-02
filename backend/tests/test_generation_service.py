import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.exceptions import InvalidModelResponseError
from app.schemas.generation import GenerateRequest
from app.schemas.product import ProductInput
from app.services import generation_service
from app.services.generation_service import build_user_content, generate_card, system_prompt


def run(coro):
    return asyncio.run(coro)


def make_payload(**overrides) -> GenerateRequest:
    product = {
        "name": "Термометр биметаллический ТБ-63",
        "manufacturer": "Теплоприбор",
        "specs": {"диапазон измерений": "0–120 °C"},
        "description": "Термометр для систем отопления.",
    }
    product.update(overrides)
    return GenerateRequest(provider="openai", api_key="sk-x", product=product)


def make_card_json(**overrides) -> str:
    card = {
        "seo_title": "Термометр ТБ-63",
        "seo_description": "о" * 900,
        "characteristics": [{"name": "Диапазон", "value": "0–120 °C"}],
        "search_queries": ["термометр купить", "термометр ТБ-63", "термометр отопления"],
        "commercial_block": "Подходит для котельных.",
        "missing_data": [],
    }
    card.update(overrides)
    return json.dumps(card, ensure_ascii=False)


def mock_provider(*texts):
    provider = AsyncMock()
    provider.generate_text = AsyncMock(side_effect=list(texts))
    return provider


def test_success_first_try():
    provider = mock_provider(make_card_json())
    with patch.object(generation_service, "get_provider", return_value=provider):
        card = run(generate_card(make_payload()))
    assert card.seo_title == "Термометр ТБ-63"
    provider.generate_text.assert_awaited_once()
    kwargs = provider.generate_text.await_args.kwargs
    assert kwargs["api_key"] == "sk-x"
    assert "ТБ-63" in kwargs["user_content"]
    assert kwargs["system_prompt"] == system_prompt()


def test_repair_retry_then_success():
    provider = mock_provider("not json", make_card_json())
    with patch.object(generation_service, "get_provider", return_value=provider):
        card = run(generate_card(make_payload()))
    assert card.seo_title == "Термометр ТБ-63"
    assert provider.generate_text.await_count == 2
    retry_kwargs = provider.generate_text.await_args.kwargs
    assert "не прошёл проверку" in retry_kwargs["user_content"]
    assert "ТБ-63" in retry_kwargs["user_content"]


def test_exhausted_retries():
    provider = mock_provider("bad", "still bad", "worse")
    with (
        patch.object(generation_service, "get_provider", return_value=provider),
        pytest.raises(InvalidModelResponseError) as exc_info,
    ):
        run(generate_card(make_payload()))
    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "invalid_model_response"
    assert provider.generate_text.await_count == 3


def test_incomplete_answer_triggers_repair():
    provider = mock_provider(
        make_card_json(characteristics=[]),
        make_card_json(),
    )
    with patch.object(generation_service, "get_provider", return_value=provider):
        card = run(generate_card(make_payload()))
    assert card.seo_title == "Термометр ТБ-63"
    assert provider.generate_text.await_count == 2


def test_missing_data_preserved():
    provider = mock_provider(make_card_json(missing_data=["присоединение", "класс точности"]))
    with patch.object(generation_service, "get_provider", return_value=provider):
        card = run(generate_card(make_payload()))
    assert card.missing_data == ["присоединение", "класс точности"]


def test_prompt_has_core_rules():
    prompt = system_prompt()
    assert "missing_data" in prompt
    assert "данных нет" in prompt
    assert "только JSON" in prompt
    assert "800" in prompt
    assert "СХЕМА ОТВЕТА" in prompt
    assert '"seo_title"' in prompt
    assert '"search_queries"' in prompt


def test_examples_parse():
    examples = Path(__file__).parent.parent / "examples"
    for name in ("product_manometer.json", "product_thermometer.json"):
        raw = json.loads((examples / name).read_text(encoding="utf-8"))
        assert ProductInput(**raw).name


def test_user_content_is_product_json():
    content = build_user_content(make_payload())
    assert content.startswith("<<<ДАННЫЕ>>>\n")
    assert content.endswith("\n<<<КОНЕЦ ДАННЫХ>>>")
    inner = content.split("<<<ДАННЫЕ>>>\n")[1].rsplit("\n<<<КОНЕЦ ДАННЫХ>>>", 1)[0]
    assert json.loads(inner)["name"].startswith("Термометр")


def test_invented_value_triggers_repair():
    provider = mock_provider(
        make_card_json(characteristics=[{"name": "Материал корпуса", "value": "титановый сплав"}]),
        make_card_json(),
    )
    with patch.object(generation_service, "get_provider", return_value=provider):
        card = run(generate_card(make_payload()))
    assert card.seo_title == "Термометр ТБ-63"
    assert provider.generate_text.await_count == 2
    retry_kwargs = provider.generate_text.await_args.kwargs
    assert "не подтверждены" in retry_kwargs["user_content"]


def test_invented_value_exhausted():
    bad = make_card_json(characteristics=[{"name": "Материал корпуса", "value": "титановый сплав"}])
    provider = mock_provider(bad, bad, bad)
    with (
        patch.object(generation_service, "get_provider", return_value=provider),
        pytest.raises(InvalidModelResponseError) as exc_info,
    ):
        run(generate_card(make_payload()))
    assert exc_info.value.status_code == 422
    assert "Материал корпуса" in str(exc_info.value)
