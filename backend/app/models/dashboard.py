from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict
from .common import Money
from .integrations import IntegrationConnection


class UpcomingItem(BaseModel):
    subscriptionId: str
    name: str
    date: str
    amount: Optional[Money] = None

    model_config = ConfigDict(from_attributes=True)


class RecentChangeItem(BaseModel):
    subscriptionId: str
    name: str
    kind: Literal["new", "price_change"]
    date: str
    detail: str

    model_config = ConfigDict(from_attributes=True)


class SpendByCategoryItem(BaseModel):
    category: str
    monthly: Money

    model_config = ConfigDict(from_attributes=True)


class DashboardSummary(BaseModel):
    monthlyRecurringSpend: Money
    annualizedSpend: Money
    subscriptionCount: int
    candidateCount: int
    openFindingsCount: int
    potentialSavings: Money
    userEstimatedSavings: Money
    upcoming: List[UpcomingItem]
    recentChanges: List[RecentChangeItem]
    spendByCategory: List[SpendByCategoryItem]
    connections: List[IntegrationConnection]

    model_config = ConfigDict(from_attributes=True)
