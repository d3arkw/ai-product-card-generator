from app.config import get_settings


def test_model_for_defaults():
    settings = get_settings()
    assert settings.model_for("routerai", "cheap") == "inclusionai/ling-3.0-flash"
    assert settings.model_for("routerai", "medium") == "qwen/qwen3.7-flash"
    assert settings.model_for("routerai", "expensive") == "minimax/minimax-m3.1-flash"
    assert settings.model_for("openai", "cheap") == settings.openai_model_cheap
    assert settings.model_for("gemini", "cheap") == settings.gemini_model_cheap


def test_model_for_legacy_alias(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "openai_model", "legacy-model")
    assert settings.model_for("openai", "cheap") == "legacy-model"
    assert settings.model_for("openai", "medium") == settings.openai_model_medium
