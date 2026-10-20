import os
import threading
from typing import Generator
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine, get_db
from models import Connection, Finding, Subscription, Transaction
from repositories.base import (
    ConnectionRepository,
    FindingRepository,
    SubscriptionRepository,
    TransactionRepository,
)
from repositories.sqlalchemy import (
    SqlAlchemyConnectionRepository,
    SqlAlchemyFindingRepository,
    SqlAlchemySubscriptionRepository,
    SqlAlchemyTransactionRepository,
)
from schemas import (
    BillingEvidenceResponse,
    ConnectionResponse,
    FindingResponse,
    Money,
    SubscriptionResponse,
    TransactionResponse,
)

_seed_subs = {
    "sub_figma": SubscriptionResponse(
        id="sub_figma",
        name="Figma Professional",
        vendorDomain="figma.com",
        category="Design",
        status="active",
        billingInterval="monthly",
        amount=Money(amountMinor=1500, currency="USD"),
        monthlyEquivalent=Money(amountMinor=1500, currency="USD"),
        nextRenewalDate="2026-10-27",
        confidence=0.97,
        explanation="Monthly design seat",
        lastChargeDate="2026-09-27",
        transactions=[
            TransactionResponse(
                id="tx_figma_1",
                connectionId="conn_bank_1",
                accountName="Chase Business Checking",
                date="2026-09-27",
                descriptionRaw="FIGMA *DESIGN",
                amount=Money(amountMinor=-1500, currency="USD"),
                status="posted",
                isRecurringCandidate=True,
            )
        ],
        evidence=[
            BillingEvidenceResponse(
                id="ev_figma_1",
                subscriptionId="sub_figma",
                senderDomain="figma.com",
                subject="Your Figma invoice",
                receivedAt="2026-09-27T10:00:00Z",
                confidence=0.98,
            )
        ],
    ),
    "sub_adobe": SubscriptionResponse(
        id="sub_adobe",
        name="Adobe Creative Cloud",
        vendorDomain="adobe.com",
        category="Design",
        status="candidate",
        billingInterval="monthly",
        amount=Money(amountMinor=5999, currency="USD"),
        monthlyEquivalent=Money(amountMinor=5999, currency="USD"),
        nextRenewalDate="2026-10-30",
        confidence=0.94,
        explanation="Overlaps with Figma",
        lastChargeDate="2026-09-30",
    ),
}

_seed_findings = {
    "fnd_dup": FindingResponse(
        id="fnd_dup",
        subscriptionId="sub_adobe",
        subscriptionName="Adobe Creative Cloud",
        type="duplicate_service",
        severity="high",
        status="open",
        title="Duplicate design suite",
        explanation="Adobe and Figma billed concurrently",
        potentialSavings=Money(amountMinor=5999, currency="USD"),
        createdAt="2026-10-18T10:00:00Z",
    )
}

_seed_connections = {
    "conn_bank_1": ConnectionResponse(
        id="conn_bank_1",
        name="Chase Business Checking",
        type="bank",
        provider="plaid",
        status="connected",
        lastSyncedAt="2026-10-20T05:00:00Z",
    )
}

_init_lock = threading.Lock()
_db_initialized = False


def ensure_db_initialized():
    global _db_initialized
    if not _db_initialized:
        with _init_lock:
            if not _db_initialized:
                Base.metadata.create_all(bind=engine)
                with SessionLocal() as session:
                    existing_sub = session.scalars(select(Subscription)).first()
                    if existing_sub is None:
                        conn_repo = SqlAlchemyConnectionRepository(session)
                        sub_repo = SqlAlchemySubscriptionRepository(session)
                        finding_repo = SqlAlchemyFindingRepository(session)
                        for conn in _seed_connections.values():
                            conn_repo.add(conn)
                        for sub in _seed_subs.values():
                            sub_repo.add(sub)
                        for finding in _seed_findings.values():
                            finding_repo.add(finding)
                _db_initialized = True


def get_subscription_repo(db: Session = Depends(get_db)) -> SubscriptionRepository:
    ensure_db_initialized()
    return SqlAlchemySubscriptionRepository(db)


def get_finding_repo(db: Session = Depends(get_db)) -> FindingRepository:
    ensure_db_initialized()
    return SqlAlchemyFindingRepository(db)


def get_transaction_repo(db: Session = Depends(get_db)) -> TransactionRepository:
    ensure_db_initialized()
    return SqlAlchemyTransactionRepository(db)


def get_connection_repo(db: Session = Depends(get_db)) -> ConnectionRepository:
    ensure_db_initialized()
    return SqlAlchemyConnectionRepository(db)
