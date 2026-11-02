from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Несекретные настройки приложения"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Product Card Generator"
    openai_model: str | None = None
    openai_model_cheap: str = "gpt-5.4-mini-2026-03-17"
    openai_model_medium: str = "gpt-5.4-2026-03-17"
    openai_model_expensive: str = "gpt-5.4-pro-2026-03-17"
    gemini_model: str | None = None
    gemini_model_cheap: str = "gemini-2.5-flash-lite"
    gemini_model_medium: str = "gemini-3.8-flash"
    gemini_model_expensive: str = "gemini-2.5-pro"
    routerai_model: str | None = None
    routerai_model_cheap: str = "inclusionai/ling-3.0-flash"
    routerai_model_medium: str = "qwen/qwen3.7-flash"
    routerai_model_expensive: str = "minimax/minimax-m3.1-flash"
    routerai_base_url: str = "https://routerai.ru/api/v1"
    request_timeout_seconds: int = 60
    max_repair_retries: int = 2
    cors_origins: str = "*"

    model_tiers: tuple[str, ...] = ("cheap", "medium", "expensive")

    def model_for(self, provider: str, tier: str) -> str:
        if tier == "cheap":
            legacy = getattr(self, f"{provider}_model", None)
            if legacy:
                return legacy
        return getattr(self, f"{provider}_model_{tier}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
