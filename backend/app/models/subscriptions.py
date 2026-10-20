from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict
from .common import Money
from .transactions import Transaction

BillingInterval = Literal["weekly", "monthly", "quarterly", "annual", "irregular", "unknown"]
SubscriptionStatus = Literal["candidate", "confirmed", "dismissed", "inactive"]
EvidenceType = Literal["invoice", "receipt", "renewal", "cancellation", "other"]


class EmailEvidence(BaseModel):
    id: str
    receivedAt: str
    senderDomain: Optional[str] = None
    subjectMinimized: Optional[str] = None
    evidenceType: EvidenceType
    amount: Optional[Money] = None
    invoiceDate: Optional[str] = None
    extractionConfidence: float
    matchScore: float
    matchStatus: Literal["suggested", "confirmed", "rejected"]
    matchReason: str

    model_config = ConfigDict(from_attributes=True)


class Subscription(BaseModel):
    id: str
    vendorName: str
    vendorDomain: Optional[str] = None
    category: Optional[str] = None
    displayName: str
    status: SubscriptionStatus
    billingInterval: BillingInterval
    expectedAmount: Optional[Money] = None
    monthlyEquivalent: Optional[Money] = None
    estimatedNextChargeAt: Optional[str] = None
    detectionConfidence: float
    detectionExplanation: str
    lastDetectedAt: str
    note: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionPatch(BaseModel):
    displayName: Optional[str] = None
    category: Optional[str] = None
    billingInterval: Optional[BillingInterval] = None
    note: Optional[str] = None
    status: Optional[SubscriptionStatus] = None


class FindingBrief(BaseModel):
    id: str
    title: str
    findingType: str
    severity: str
    status: str
    estimatedImpact: Optional[Money] = None

    model_config = ConfigDict(from_attributes=True)


class SubscriptionDetail(Subscription):
    transactions: List[Transaction] = []
    evidence: List[EmailEvidence] = []
    findings: List[FindingBrief] = []

    model_config = ConfigDict(from_attributes=True)
