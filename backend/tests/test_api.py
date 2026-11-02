from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.generation import ProductCard

client = TestClient(app, raise_server_exceptions=False)


def make_payload() -> dict:
    return {
        "provider": "openai",
        "api_key": "sk-test",
        "product": {
            "name": "Манометр показывающий DM 02",
            "manufacturer": "Манотомь",
            "specs": {"диапазон измерений": "0–1,6 МПа"},
            "description": "Прибор для измерения избыточного давления.",
        },
    }


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "up"}


def test_generate_returns_card():
    card = ProductCard(
        seo_title="Термометр ТБ-63",
        seo_description="о" * 900,
        characteristics=[{"name": "Диапазон", "value": "0–120 °C"}],
        search_queries=["термометр купить", "термометр ТБ-63", "термометр отопления"],
        commercial_block="Подходит для котельных.",
        missing_data=[],
    )
    with patch("app.main.generate_card", AsyncMock(return_value=card)):
        response = client.post("/api/v1/generate", json=make_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["seo_title"] == "Термометр ТБ-63"


def test_missing_api_key_rejected():
    payload = make_payload()
    del payload["api_key"]
    response = client.post("/api/v1/generate", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_whitespace_api_key_rejected():
    payload = make_payload()
    payload["api_key"] = "   "
    response = client.post("/api/v1/generate", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_unknown_model_tier_rejected():
    payload = make_payload()
    payload["model_tier"] = "ultra"
    response = client.post("/api/v1/generate", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_models_endpoint_lists_tiers():
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    models = response.json()["models"]
    assert set(models) == {"openai", "gemini", "routerai"}
    for provider_models in models.values():
        assert set(provider_models) == {"cheap", "medium", "expensive"}
        assert all(isinstance(model, str) and model for model in provider_models.values())
    assert models["routerai"]["cheap"] == "inclusionai/ling-3.0-flash"


def test_unknown_provider_rejected():
    payload = make_payload()
    payload["provider"] = "anthropic"
    response = client.post("/api/v1/generate", json=payload)
    assert response.status_code == 422


def test_empty_product_name_rejected():
    payload = make_payload()
    payload["product"]["name"] = ""
    response = client.post("/api/v1/generate", json=payload)
    assert response.status_code == 422
