from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=300)
    manufacturer: str = Field(default="", max_length=300)
    specs: dict[str, str] = Field(default_factory=dict)
    description: str = Field(default="", max_length=20000)

    @field_validator("name", "manufacturer", "description", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("specs", mode="before")
    @classmethod
    def clean_specs(cls, value: dict[str, str]) -> dict[str, str]:
        return {key.strip(): item.strip() for key, item in value.items() if key.strip()}
