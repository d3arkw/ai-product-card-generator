from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from app.schemas.product import ProductInput


class GenerateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: Literal["openai", "gemini", "routerai"]
    model_tier: Literal["cheap", "medium", "expensive"] = "cheap"
    api_key: SecretStr = Field(min_length=1, max_length=500)
    product: ProductInput

    @field_validator("api_key")
    @classmethod
    def _strip_key(cls, value: SecretStr) -> SecretStr:
        text = value.get_secret_value().strip()
        if not text:
            raise ValueError("API-ключ не должен быть пустым")
        return SecretStr(text)


class Characteristic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    value: str = Field(min_length=1, max_length=1000)


class ProductCard(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seo_title: str = Field(min_length=1, max_length=70)
    seo_description: str = Field(min_length=800, max_length=1200)
    characteristics: list[Characteristic] = Field(min_length=1)
    search_queries: list[str] = Field(min_length=3, max_length=5)
    commercial_block: str = Field(min_length=1, max_length=2000)
    missing_data: list[str] = Field(default_factory=list)


class CardResponse(BaseModel):
    ok: Literal[True] = True
    data: ProductCard
