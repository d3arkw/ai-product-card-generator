from app.config import get_settings


def test_model_for_defaults():
    settings = get_settings()
    assert settings.model_for("routerai", "cheap") == "inclusionai/ling-3.0-flash"
    assert settings.model_for("routerai", "medium") == "qwen/qwen3.7-flash"
    assert settings.model_for("routerai", "expensive") == "minimax/minimax-m3.1-flash"
    assert settings.model_for("openai", "cheap") == settings.openai_model_cheap
    assert settings.model_for("gemini", "cheap") == "gemini-3.5-flash-lite"
    assert settings.model_for("gemini", "medium") == "gemini-3.6-flash"
    assert settings.model_for("gemini", "expensive") == "gemini-3.8-flash"


def test_model_for_legacy_alias(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "openai_model", "legacy-model")
    assert settings.model_for("openai", "cheap") == "legacy-model"
    assert settings.model_for("openai", "medium") == settings.openai_model_medium
