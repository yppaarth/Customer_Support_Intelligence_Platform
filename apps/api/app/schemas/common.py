from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)


class ErrorResponse(BaseModel):
    detail: str
    correlation_id: str | None = None


class Timestamped(ORMModel):
    created_at: datetime
