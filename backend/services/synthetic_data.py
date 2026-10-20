from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple
from schemas import (
    BillingEvidenceResponse,
    ConnectionResponse,
    Money,
    SubscriptionResponse,
    TransactionResponse,
)

NOW = datetime(2026, 10, 20, 12, 0, 0, tzinfo=timezone.utc)


def days_ago(days: float) -> str:
    return (NOW - timedelta(days=days)).strftime("%Y-%m-%d")


def iso_ago(days: float) -> str:
    return (NOW - timedelta(days=days)).isoformat()


def generate_synthetic_data() -> Dict[str, Any]:
    """
    Generates at least 25 realistic raw transaction records spanning 90 days
    across multiple merchants (AWS, GitHub, Figma, Adobe, Google Workspace),
    including variations: steady amounts, price increases, trial conversions, and irregular charges.
    Also produces parsed billing evidence records matching transaction timestamps.
    """
    transactions: List[TransactionResponse] = []
    evidence: List[BillingEvidenceResponse] = []

    # 1. Figma: Steady amount ($15/mo for 3 cycles)
    for i in range(3):
        days = (3 - i) * 30
        tx = TransactionResponse(
            id=f"tx_figma_{i}",
            connectionId="conn_bank_1",
            accountName="Chase Business Checking",
            date=days_ago(days),
            descriptionRaw="FIGMA.COM *INV48201",
            merchantNormalized="Figma",
            amount=Money(amountMinor=-1500, currency="USD"),
            status="posted",
            isRecurringCandidate=True,
        )
        transactions.append(tx)
        ev = BillingEvidenceResponse(
            id=f"ev_figma_{i}",
            subscriptionId="sub_figma",
            senderDomain="figma.com",
            subject="Your Figma invoice is ready",
            receivedAt=iso_ago(days + 0.1),
            snippet="Payment received for Figma Professional seat.",
            extractedAmountMinor=1500,
            confidence=0.98,
        )
        evidence.append(ev)

    # 2. Notion Plus: Quiet price increase ($10 -> $12/mo)
    notion_amounts = [1000, 1000, 1200]
    for i, amt in enumerate(notion_amounts):
        days = (3 - i) * 30 - 2
        transactions.append(
            TransactionResponse(
                id=f"tx_notion_{i}",
                connectionId="conn_bank_1",
                accountName="Chase Business Checking",
                date=days_ago(days),
                descriptionRaw="NOTION LABS INC WWW.NOTION.SO",
                merchantNormalized="Notion",
                amount=Money(amountMinor=-amt, currency="USD"),
                status="posted",
                isRecurringCandidate=True,
            )
        )
        evidence.append(
            BillingEvidenceResponse(
                id=f"ev_notion_{i}",
                subscriptionId="sub_notion",
                senderDomain="notion.so",
                subject="Notice of upcoming rate adjustment" if i == 1 else "Notion Plus receipt",
                receivedAt=iso_ago(days + 0.2),
                snippet=f"Billed ${amt/100:.2f} for Notion Plus workspace.",
                extractedAmountMinor=amt,
                confidence=0.95,
            )
        )

    # 3. Notion AI: Trial conversion ($0 trial -> $10/mo recurring)
    trial_days = 28
    transactions.append(
        TransactionResponse(
            id="tx_notion_ai_0",
            connectionId="conn_bank_1",
            accountName="Chase Business Checking",
            date=days_ago(trial_days),
            descriptionRaw="NOTION AI ADDON TRIAL CONV",
            merchantNormalized="Notion",
            amount=Money(amountMinor=-1000, currency="USD"),
            status="posted",
            isRecurringCandidate=True,
        )
    )
    evidence.append(
        BillingEvidenceResponse(
            id="ev_notion_ai_0",
            subscriptionId="sub_notion_ai",
            senderDomain="notion.so",
            subject="Your 30-day Notion AI trial has ended",
            receivedAt=iso_ago(trial_days + 0.5),
            snippet="Your free trial concluded and converted to a paid monthly add-on.",
            extractedAmountMinor=1000,
            confidence=0.96,
        )
    )

    # 4. Adobe Creative Cloud: Steady $59.99/mo (3 cycles)
    for i in range(3):
        days = (3 - i) * 30 - 5
        transactions.append(
            TransactionResponse(
                id=f"tx_adobe_{i}",
                connectionId="conn_bank_1",
                accountName="Chase Business Checking",
                date=days_ago(days),
                descriptionRaw="ADOBE *CREATIVE CLOUD",
                merchantNormalized="Adobe",
                amount=Money(amountMinor=-5999, currency="USD"),
                status="posted",
                isRecurringCandidate=True,
            )
        )
        evidence.append(
            BillingEvidenceResponse(
                id=f"ev_adobe_{i}",
                subscriptionId="sub_adobe",
                senderDomain="adobe.com",
                subject="Your Adobe invoice is available",
                receivedAt=iso_ago(days + 0.1),
                snippet="Adobe Creative Cloud All Apps billed at $59.99.",
                extractedAmountMinor=5999,
                confidence=0.97,
            )
        )

    # 5. AWS: Irregular charges (usage-based)
    aws_amounts = [4210, 4850, 4902]
    for i, amt in enumerate(aws_amounts):
        days = (3 - i) * 30 + 1
        transactions.append(
            TransactionResponse(
                id=f"tx_aws_{i}",
                connectionId="conn_bank_1",
                accountName="Chase Business Checking",
                date=days_ago(days),
                descriptionRaw="AMAZON WEB SERVICES AWS.AMAZON.CO",
                merchantNormalized="Amazon Web Services",
                amount=Money(amountMinor=-amt, currency="USD"),
                status="posted",
                isRecurringCandidate=True,
            )
        )
        evidence.append(
            BillingEvidenceResponse(
                id=f"ev_aws_{i}",
                subscriptionId="sub_aws",
                senderDomain="aws.amazon.com",
                subject="Amazon Web Services Invoice #AWS-99120",
                receivedAt=iso_ago(days + 0.2),
                snippet=f"Monthly AWS usage invoice: ${amt/100:.2f}.",
                extractedAmountMinor=amt,
                confidence=0.93,
            )
        )

    # 6. GitHub Team: Steady $21.00/mo (3 cycles)
    for i in range(3):
        days = (3 - i) * 30 - 8
        transactions.append(
            TransactionResponse(
                id=f"tx_github_{i}",
                connectionId="conn_bank_1",
                accountName="Chase Business Checking",
                date=days_ago(days),
                descriptionRaw="GITHUB *TEAM SEATS",
                merchantNormalized="GitHub",
                amount=Money(amountMinor=-2100, currency="USD"),
                status="posted",
                isRecurringCandidate=True,
            )
        )
        evidence.append(
            BillingEvidenceResponse(
                id=f"ev_github_{i}",
                subscriptionId="sub_github",
                senderDomain="github.com",
                subject="Your GitHub receipt for Team plan",
                receivedAt=iso_ago(days + 0.1),
                snippet="Thank you for using GitHub. Billed $21.00.",
                extractedAmountMinor=2100,
                confidence=0.98,
            )
        )

    # 7. Google Workspace: Steady $18.00/mo (3 cycles)
    for i in range(3):
        days = (3 - i) * 30 - 10
        transactions.append(
            TransactionResponse(
                id=f"tx_google_{i}",
                connectionId="conn_bank_1",
                accountName="Chase Business Checking",
                date=days_ago(days),
                descriptionRaw="GOOGLE *WORKSPACE_GSUITE",
                merchantNormalized="Google Workspace",
                amount=Money(amountMinor=-1800, currency="USD"),
                status="posted",
                isRecurringCandidate=True,
            )
        )
        evidence.append(
            BillingEvidenceResponse(
                id=f"ev_google_{i}",
                subscriptionId="sub_google",
                senderDomain="google.com",
                subject="Your Google Workspace monthly invoice",
                receivedAt=iso_ago(days + 0.1),
                snippet="Google Workspace Business Standard billed $18.00.",
                extractedAmountMinor=1800,
                confidence=0.99,
            )
        )

    # 8. Miscellaneous one-off noise (to test filtering)
    noise = [
        ("UBER *TRIP RIDE", -2450),
        ("STAPLES 0482 SUPPLIES", -6712),
        ("DELTA AIR 0820 FLIGHT", -41200),
        ("STARBUCKS #1182", -675),
        ("OFFICE DEPOT", -3499),
        ("USPS POSTAGE", -1840),
    ]
    for i, (desc, amt) in enumerate(noise):
        transactions.append(
            TransactionResponse(
                id=f"tx_noise_{i}",
                connectionId="conn_bank_1",
                accountName="Chase Business Checking",
                date=days_ago(15 + i * 10),
                descriptionRaw=desc,
                merchantNormalized=None,
                amount=Money(amountMinor=amt, currency="USD"),
                status="posted",
                isRecurringCandidate=False,
            )
        )

    return {
        "transactions": transactions,
        "evidence": evidence,
    }


def seed_synthetic_data(repositories: Any) -> int:
    """
    Populates the provided repositories with synthetic data.
    Works with both in-memory and database-backed repository bundles.
    """
    data = generate_synthetic_data()
    tx_repo = getattr(repositories, "tx_repo", getattr(repositories, "transactions", None))
    count = 0
    if tx_repo and hasattr(tx_repo, "add"):
        for tx in data["transactions"]:
            tx_repo.add(tx)
            count += 1
    return count
