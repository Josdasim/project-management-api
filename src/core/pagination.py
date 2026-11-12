from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    total: int
    page: int
    page_size: int


class PaginationParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: Annotated[int, Field(ge=1)] = 1
    page_size: Annotated[int, Field(ge=1, le=100)] = 20


class PageResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
