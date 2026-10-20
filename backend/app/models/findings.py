from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict
from .common import Money
from .transactions import Transaction
from .subscriptions import EmailEvidence

FindingType = Literal[
    "possible_duplicate",
    "price_increase",
    "unexpected_charge",
    "low_evidence",
    "renewal_approaching",
    "unclear_vendor",
]
FindingStatus = Literal["new", "reviewing", "confirmed", "dismissed", "resolved"]
Severity = Literal["low", "medium", "high"]


class Finding(BaseModel):
    id: str
    subscriptionId: Optional[str] = None
    subscriptionName: Optional[str] = None
    findingType: FindingType
    severity: Severity
    status: FindingStatus
    title: string = ""
    title: str
    explanation: str
    estimatedImpact: Optional[Money] = None
    confidence: float
    ruleVersion: str
    createdAt: str
    updatedAt: str

    model_config = ConfigDict(from_attributes=True)


class FindingEvidenceItem(BaseModel):
    role: Literal["trigger", "supporting", "context"]
    explanation: str
    transaction: Optional[Transaction] = None
    email: Optional[EmailEvidence] = None

    model_config = ConfigDict(from_attributes=True)


class UserReview(BaseModel):
    id: str
    decision: Literal["confirm", "dismiss", "mark_reviewing", "resolve"]
    note: Optional[str] = None
    estimatedSavings: Optional[Money] = None
    createdAt: str

    model_config = ConfigDict(from_attributes=True)


class ReviewInput(BaseModel):
    decision: Literal["confirm", "dismiss", "mark_reviewing", "resolve"]
    note: Optional[str] = None
    estimatedSavings: Optional[Money] = None


class FindingDetail(Finding):
    evidence: List[FindingEvidenceItem] = []
    reviews: List[UserReview] = []

    model_config = ConfigDict(from_attributes=True)
