from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict
from .common import Money

TransactionStatus = Literal["pending", "posted", "reversed", "removed"]


class Transaction(BaseModel):
    id: str
    connectionId: str
    accountName: str
    postedAt: str
    amount: Money
    descriptionRaw: str
    merchantNormalized: Optional[str] = None
    status: TransactionStatus
    isRecurringCandidate: bool
    subscriptionId: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TransactionQuery(BaseModel):
    q: Optional[str] = None
    status: Optional[TransactionStatus] = None
    subscriptionId: Optional[str] = None
    page: int = 1
    pageSize: int = 50
