from typing import Generic, List, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Money(BaseModel):
    amountMinor: int
    currency: str = "USD"

    model_config = ConfigDict(from_attributes=True)


class Paginated(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    pageSize: int
    hasMore: bool

    model_config = ConfigDict(from_attributes=True)
