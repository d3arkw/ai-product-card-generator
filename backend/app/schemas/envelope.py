from typing import Literal

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: list[str] = Field(default_factory=list)


class ErrorEnvelope(BaseModel):
    ok: Literal[False] = False
    error: ApiError
