from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Несекретные настройки приложения"""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI Product Card Generator"
    openai_model: str = "gpt-5.4-mini-2026-03-17"
    gemini_model: str = "gemini-3.8-flash"
    routerai_model: str = "inclusionai/ling-3.0-flash"
    routerai_base_url: str = "https://routerai.ru/api/v1"
    request_timeout_seconds: int = 60
    max_repair_retries: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()
