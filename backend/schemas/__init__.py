from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

BillingInterval = Literal["weekly", "monthly", "quarterly", "annual", "irregular"]
FindingType = Literal[
    "forgotten_charge",
    "trial_conversion",
    "price_increase",
    "duplicate_service",
    "renewal_approaching",
]
UserDecision = Literal["confirmed_waste", "marked_useful", "snoozed", "dismissed"]


class Money(BaseModel):
    amountMinor: int = Field(..., description="Amount in minor units, e.g. cents")
    currency: str = Field(default="USD", description="ISO 4217 currency code")

    model_config = ConfigDict(from_attributes=True)


class FindingActionRequest(BaseModel):
    decision: UserDecision
    note: Optional[str] = None
    snoozeDays: int = 30


class BillingEvidenceResponse(BaseModel):
    id: str
    subscriptionId: str
    senderDomain: str
    subject: str
    receivedAt: str
    snippet: Optional[str] = ""
    extractedAmountMinor: Optional[int] = None
    confidence: float

    model_config = ConfigDict(from_attributes=True)


class TransactionResponse(BaseModel):
    id: str
    connectionId: str
    accountName: str
    date: str
    descriptionRaw: str
    merchantNormalized: Optional[str] = None
    amount: Money
    status: Literal["posted", "pending"]
    isRecurringCandidate: bool
    subscriptionId: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionResponse(BaseModel):
    id: str
    name: str
    vendorDomain: Optional[str] = None
    category: str
    status: Literal["active", "candidate", "confirmed", "dismissed", "cancelled"]
    billingInterval: BillingInterval
    amount: Money
    monthlyEquivalent: Money
    nextRenewalDate: Optional[str] = None
    confidence: float
    explanation: str
    lastChargeDate: str
    transactions: List[TransactionResponse] = []
    evidence: List[BillingEvidenceResponse] = []

    model_config = ConfigDict(from_attributes=True)


class FindingResponse(BaseModel):
    id: str
    subscriptionId: str
    subscriptionName: str
    type: FindingType
    severity: Literal["low", "medium", "high"]
    status: Literal["open", "confirmed_waste", "marked_useful", "snoozed", "dismissed"]
    title: str
    explanation: str
    potentialSavings: Money
    confirmedSavings: Optional[Money] = None
    decision: Optional[UserDecision] = None
    decisionNote: Optional[str] = None
    decisionAt: Optional[str] = None
    evidence: List[BillingEvidenceResponse] = []
    createdAt: str

    model_config = ConfigDict(from_attributes=True)


class RenewalResponse(BaseModel):
    id: str
    subscriptionId: str
    vendorName: str
    amount: Money
    dueDate: str
    cadence: BillingInterval
    evidenceTag: str
    hasReminder: bool
    timeWindow: Literal["next_7_days", "next_30_days", "later_this_quarter"]

    model_config = ConfigDict(from_attributes=True)


class ConnectionResponse(BaseModel):
    id: str
    name: str
    type: Literal["bank", "email"]
    provider: str
    status: Literal["connected", "syncing", "error", "disconnected"]
    lastSyncedAt: Optional[str] = None
    accountMask: Optional[str] = None
    emailAddress: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OverviewMetricsResponse(BaseModel):
    monthlyRecurringSpend: Money
    annualizedSpend: Money
    activeSubscriptionCount: int
    potentialSavings: Money
    confirmedSavings: Money
    openFindingsCount: int
    upcomingRenewalsCount: int

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: Optional[dict] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str = "SubTracker API"
    version: str = "1.0.0"
