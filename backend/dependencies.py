from typing import Generator
from repositories.base import (
    ConnectionRepository,
    FindingRepository,
    SubscriptionRepository,
    TransactionRepository,
)
from repositories.memory import (
    InMemoryConnectionRepository,
    InMemoryFindingRepository,
    InMemorySubscriptionRepository,
    InMemoryTransactionRepository,
)
from schemas import (
    BillingEvidenceResponse,
    ConnectionResponse,
    FindingResponse,
    Money,
    SubscriptionResponse,
    TransactionResponse,
)

# Seed in-memory repositories
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

_sub_repo = InMemorySubscriptionRepository(_seed_subs)
_finding_repo = InMemoryFindingRepository(_seed_findings)
_tx_repo = InMemoryTransactionRepository()
_conn_repo = InMemoryConnectionRepository(_seed_connections)


def get_subscription_repo() -> SubscriptionRepository:
    return _sub_repo


def get_finding_repo() -> FindingRepository:
    return _finding_repo


def get_transaction_repo() -> TransactionRepository:
    return _tx_repo


def get_connection_repo() -> ConnectionRepository:
    return _conn_repo
