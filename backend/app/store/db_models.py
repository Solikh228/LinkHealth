from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..database import Base
from ..models import (
    EmailEvidence,
    Finding,
    FindingBrief,
    IntegrationConnection,
    Money,
    Subscription,
    Transaction,
    User,
    UserReview,
    Workspace,
)


class UserDB(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(String(64), nullable=False)

    workspaces = relationship("WorkspaceDB", back_populates="owner", cascade="all, delete-orphan")

    def to_pydantic(self) -> User:
        return User(
            id=self.id,
            email=self.email,
            createdAt=self.created_at,
        )


class WorkspaceDB(Base):
    __tablename__ = "workspaces"

    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    owner_user_id = Column(String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    base_currency = Column(String(10), nullable=False, default="USD")
    created_at = Column(String(64), nullable=False)

    owner = relationship("UserDB", back_populates="workspaces")

    def to_pydantic(self) -> Workspace:
        return Workspace(
            id=self.id,
            name=self.name,
            ownerUserId=self.owner_user_id,
            baseCurrency=self.base_currency,
            createdAt=self.created_at,
        )


class IntegrationConnectionDB(Base):
    __tablename__ = "integration_connections"

    id = Column(String(64), primary_key=True)
    kind = Column(String(32), nullable=False)
    provider = Column(String(64), nullable=False)
    display_name = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False)
    sync_state = Column(String(32), nullable=False)
    scopes_granted = Column(JSON, nullable=False, default=list)
    last_sync_at = Column(String(64), nullable=True)
    last_sync_status = Column(String(32), nullable=True)
    created_at = Column(String(64), nullable=False)

    def to_pydantic(self) -> IntegrationConnection:
        return IntegrationConnection(
            id=self.id,
            kind=self.kind,
            provider=self.provider,
            displayName=self.display_name,
            status=self.status,
            syncState=self.sync_state,
            scopesGranted=self.scopes_granted or [],
            lastSyncAt=self.last_sync_at,
            lastSyncStatus=self.last_sync_status,
            createdAt=self.created_at,
        )


class SubscriptionDB(Base):
    __tablename__ = "subscriptions"

    id = Column(String(64), primary_key=True)
    vendor_name = Column(String(255), nullable=False)
    vendor_domain = Column(String(255), nullable=True)
    category = Column(String(64), nullable=True)
    display_name = Column(String(255), nullable=False)
    status = Column(String(32), nullable=False)
    billing_interval = Column(String(32), nullable=False)
    expected_amount_minor = Column(Integer, nullable=True)
    expected_amount_currency = Column(String(10), nullable=True)
    monthly_equivalent_minor = Column(Integer, nullable=True)
    monthly_equivalent_currency = Column(String(10), nullable=True)
    estimated_next_charge_at = Column(String(64), nullable=True)
    detection_confidence = Column(Float, nullable=False, default=0.0)
    detection_explanation = Column(Text, nullable=False, default="")
    last_detected_at = Column(String(64), nullable=False)
    note = Column(Text, nullable=True)

    transactions = relationship("TransactionDB", back_populates="subscription", cascade="all, delete")
    evidence = relationship("EmailEvidenceDB", back_populates="subscription", cascade="all, delete-orphan")
    findings = relationship("FindingDB", back_populates="subscription")

    def to_pydantic(self) -> Subscription:
        expected = None
        if self.expected_amount_minor is not None:
            expected = Money(amountMinor=self.expected_amount_minor, currency=self.expected_amount_currency or "USD")
        monthly = None
        if self.monthly_equivalent_minor is not None:
            monthly = Money(amountMinor=self.monthly_equivalent_minor, currency=self.monthly_equivalent_currency or "USD")

        return Subscription(
            id=self.id,
            vendorName=self.vendor_name,
            vendorDomain=self.vendor_domain,
            category=self.category,
            displayName=self.display_name,
            status=self.status,
            billingInterval=self.billing_interval,
            expectedAmount=expected,
            monthlyEquivalent=monthly,
            estimatedNextChargeAt=self.estimated_next_charge_at,
            detectionConfidence=self.detection_confidence,
            detectionExplanation=self.detection_explanation,
            lastDetectedAt=self.last_detected_at,
            note=self.note,
        )


class TransactionDB(Base):
    __tablename__ = "transactions"

    id = Column(String(64), primary_key=True)
    connection_id = Column(String(64), ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    account_name = Column(String(255), nullable=False)
    posted_at = Column(String(64), nullable=False, index=True)
    amount_minor = Column(Integer, nullable=False)
    amount_currency = Column(String(10), nullable=False, default="USD")
    description_raw = Column(Text, nullable=False)
    merchant_normalized = Column(String(255), nullable=True)
    status = Column(String(32), nullable=False)
    is_recurring_candidate = Column(Boolean, nullable=False, default=False)
    subscription_id = Column(String(64), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)

    subscription = relationship("SubscriptionDB", back_populates="transactions")

    def to_pydantic(self) -> Transaction:
        return Transaction(
            id=self.id,
            connectionId=self.connection_id,
            accountName=self.account_name,
            postedAt=self.posted_at,
            amount=Money(amountMinor=self.amount_minor, currency=self.amount_currency),
            descriptionRaw=self.description_raw,
            merchantNormalized=self.merchant_normalized,
            status=self.status,
            isRecurringCandidate=self.is_recurring_candidate,
            subscriptionId=self.subscription_id,
        )


class EmailEvidenceDB(Base):
    __tablename__ = "email_evidence"

    id = Column(String(64), primary_key=True)
    subscription_id = Column(String(64), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    received_at = Column(String(64), nullable=False)
    sender_domain = Column(String(255), nullable=True)
    subject_minimized = Column(String(500), nullable=True)
    evidence_type = Column(String(32), nullable=False)
    amount_minor = Column(Integer, nullable=True)
    amount_currency = Column(String(10), nullable=True)
    invoice_date = Column(String(64), nullable=True)
    extraction_confidence = Column(Float, nullable=False, default=0.0)
    match_score = Column(Float, nullable=False, default=0.0)
    match_status = Column(String(32), nullable=False)
    match_reason = Column(Text, nullable=False, default="")

    subscription = relationship("SubscriptionDB", back_populates="evidence")

    def to_pydantic(self) -> EmailEvidence:
        amt = None
        if self.amount_minor is not None:
            amt = Money(amountMinor=self.amount_minor, currency=self.amount_currency or "USD")
        return EmailEvidence(
            id=self.id,
            receivedAt=self.received_at,
            senderDomain=self.sender_domain,
            subjectMinimized=self.subject_minimized,
            evidenceType=self.evidence_type,
            amount=amt,
            invoiceDate=self.invoice_date,
            extractionConfidence=self.extraction_confidence,
            matchScore=self.match_score,
            matchStatus=self.match_status,
            matchReason=self.match_reason,
        )


class FindingDB(Base):
    __tablename__ = "findings"

    id = Column(String(64), primary_key=True)
    subscription_id = Column(String(64), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    subscription_name = Column(String(255), nullable=True)
    finding_type = Column(String(64), nullable=False)
    severity = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False)
    title = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    estimated_impact_minor = Column(Integer, nullable=True)
    estimated_impact_currency = Column(String(10), nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    rule_version = Column(String(32), nullable=False)
    created_at = Column(String(64), nullable=False)
    updated_at = Column(String(64), nullable=False)

    subscription = relationship("SubscriptionDB", back_populates="findings")
    reviews = relationship("UserReviewDB", back_populates="finding", cascade="all, delete-orphan")

    def to_pydantic(self) -> Finding:
        impact = None
        if self.estimated_impact_minor is not None:
            impact = Money(amountMinor=self.estimated_impact_minor, currency=self.estimated_impact_currency or "USD")
        return Finding(
            id=self.id,
            subscriptionId=self.subscription_id,
            subscriptionName=self.subscription_name,
            findingType=self.finding_type,
            severity=self.severity,
            status=self.status,
            title=self.title,
            explanation=self.explanation,
            estimatedImpact=impact,
            confidence=self.confidence,
            ruleVersion=self.rule_version,
            createdAt=self.created_at,
            updatedAt=self.updated_at,
        )

    def to_brief(self) -> FindingBrief:
        impact = None
        if self.estimated_impact_minor is not None:
            impact = Money(amountMinor=self.estimated_impact_minor, currency=self.estimated_impact_currency or "USD")
        return FindingBrief(
            id=self.id,
            title=self.title,
            findingType=self.finding_type,
            severity=self.severity,
            status=self.status,
            estimatedImpact=impact,
        )


class UserReviewDB(Base):
    __tablename__ = "user_reviews"

    id = Column(String(64), primary_key=True)
    finding_id = Column(String(64), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True)
    decision = Column(String(32), nullable=False)
    note = Column(Text, nullable=True)
    estimated_savings_minor = Column(Integer, nullable=True)
    estimated_savings_currency = Column(String(10), nullable=True)
    created_at = Column(String(64), nullable=False)

    finding = relationship("FindingDB", back_populates="reviews")

    def to_pydantic(self) -> UserReview:
        savings = None
        if self.estimated_savings_minor is not None:
            savings = Money(amountMinor=self.estimated_savings_minor, currency=self.estimated_savings_currency or "USD")
        return UserReview(
            id=self.id,
            decision=self.decision,
            note=self.note,
            estimatedSavings=savings,
            createdAt=self.created_at,
        )
