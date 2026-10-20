from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)

    connections: Mapped[List["Connection"]] = relationship(
        "Connection", back_populates="user", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription", back_populates="user", cascade="all, delete-orphan"
    )


class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # bank, email
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # plaid, gmail, etc.
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="connected")
    last_synced_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="connections")
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="connection", cascade="all, delete-orphan"
    )
    billing_evidence: Mapped[List["BillingEvidence"]] = relationship(
        "BillingEvidence", back_populates="connection", cascade="all, delete-orphan"
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vendor_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    billing_interval: Mapped[str] = mapped_column(String(50), nullable=False)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    monthly_equivalent_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    next_renewal_date: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    last_charge_date: Mapped[str] = mapped_column(String(64), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="subscriptions")
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="subscription"
    )
    billing_evidence: Mapped[List["BillingEvidence"]] = relationship(
        "BillingEvidence", back_populates="subscription", cascade="all, delete-orphan"
    )
    findings: Mapped[List["Finding"]] = relationship(
        "Finding", back_populates="subscription", cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("provider_connection_id", "provider_transaction_id", name="uq_provider_conn_tx"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    connection_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subscription_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[str] = mapped_column(String(64), nullable=False)
    description_raw: Mapped[str] = mapped_column(Text, nullable=False)
    merchant_normalized: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="posted")
    is_recurring_candidate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    provider_connection_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_transaction_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    connection: Mapped["Connection"] = relationship("Connection", back_populates="transactions")
    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription", back_populates="transactions"
    )


class BillingEvidence(Base):
    __tablename__ = "billing_evidence"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    subscription_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    connection_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("connections.id", ondelete="CASCADE"), nullable=True, index=True
    )
    sender_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    received_at: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription", back_populates="billing_evidence"
    )
    connection: Mapped[Optional["Connection"]] = relationship(
        "Connection", back_populates="billing_evidence"
    )


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    subscription_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    subscription_name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    potential_savings_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    confirmed_savings_minor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)
    decision: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    decision_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decision_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    subscription: Mapped[Optional["Subscription"]] = relationship(
        "Subscription", back_populates="findings"
    )
    actions: Mapped[List["Action"]] = relationship(
        "Action", back_populates="finding", cascade="all, delete-orphan"
    )


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    finding_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    decision: Mapped[str] = mapped_column(String(50), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), nullable=False)

    finding: Mapped["Finding"] = relationship("Finding", back_populates="actions")
