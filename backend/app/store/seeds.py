from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple
from ..auth.security import hash_password
from ..models import (
    EmailEvidence,
    Finding,
    IntegrationConnection,
    Money,
    Subscription,
    Transaction,
    User,
    Workspace,
)

NOW = datetime(2026, 10, 19, 12, 0, 0, tzinfo=timezone.utc)


def days_ago(d: float) -> str:
    return (NOW - timedelta(days=d)).isoformat()


def days_ahead(d: float) -> str:
    return (NOW + timedelta(days=d)).isoformat()


def monthly_equivalent_minor(amount: int, interval: str) -> int:
    if interval == "weekly":
        return round(amount * 52 / 12)
    elif interval == "quarterly":
        return round(amount / 3)
    elif interval == "annual":
        return round(amount / 12)
    return amount


def get_initial_seed_data():
    default_user = User(
        id="usr_1",
        email="alex@studio.dev",
        createdAt=days_ago(400),
    )
    user_passwords = {
        default_user.id: hash_password("password123")
    }

    default_workspace = Workspace(
        id="ws_1",
        name="Alex Studio",
        ownerUserId=default_user.id,
        baseCurrency="USD",
        createdAt=days_ago(400),
    )

    connections = [
        IntegrationConnection(
            id="conn_bank",
            kind="bank",
            provider="plaid",
            displayName="Chase Business ••4821",
            status="active",
            syncState="up_to_date",
            scopesGranted=["transactions:read", "accounts:read"],
            lastSyncAt=days_ago(0.1),
            lastSyncStatus="success",
            createdAt=days_ago(120),
        ),
        IntegrationConnection(
            id="conn_gmail",
            kind="gmail",
            provider="google",
            displayName="alex@studio.dev",
            status="needs_reauth",
            syncState="needs_reauth",
            scopesGranted=["gmail.readonly"],
            lastSyncAt=days_ago(6),
            lastSyncStatus="failed",
            createdAt=days_ago(120),
        ),
    ]

    seed_subs = [
        {
            "id": "sub_figma",
            "name": "Figma Professional",
            "domain": "figma.com",
            "category": "Design",
            "interval": "monthly",
            "amounts": [1500, 1500, 1500, 1500, 1500, 1500],
            "descriptor": "FIGMA *MONTHLY SAN FRANCISCO",
            "status": "confirmed",
            "confidence": 0.97,
            "explanation": "6 charges ~30 days apart, identical amount, matched to 6 invoice emails from figma.com.",
            "nextIn": 8,
            "everyDays": 30,
            "currency": "USD",
        },
        {
            "id": "sub_notion",
            "name": "Notion Plus",
            "domain": "notion.so",
            "category": "Productivity",
            "interval": "monthly",
            "amounts": [1000, 1000, 1000, 1200, 1200, 1200],
            "descriptor": "NOTION LABS INC",
            "status": "candidate",
            "confidence": 0.91,
            "explanation": "Monthly cadence (±2 days). Amount rose from $10.00 to $12.00 three cycles ago.",
            "nextIn": 3,
            "everyDays": 30,
            "currency": "USD",
        },
        {
            "id": "sub_aws",
            "name": "Amazon Web Services",
            "domain": "aws.amazon.com",
            "category": "Infrastructure",
            "interval": "monthly",
            "amounts": [4210, 3988, 5120, 4475, 4630, 4902],
            "descriptor": "AWS EMEA aws.amazon.co",
            "status": "confirmed",
            "confidence": 0.88,
            "explanation": "Variable usage-based amounts, consistent monthly cadence on the 2nd–3rd.",
            "nextIn": 14,
            "everyDays": 30,
            "currency": "USD",
        },
        {
            "id": "sub_adobe",
            "name": "Adobe Creative Cloud",
            "domain": "adobe.com",
            "category": "Design",
            "interval": "monthly",
            "amounts": [5499, 5499, 5499, 5999, 5999, 5999],
            "descriptor": "ADOBE *CREATIVE CLD",
            "status": "candidate",
            "confidence": 0.94,
            "explanation": "Monthly cadence. Overlaps with Figma Professional in the Design category.",
            "nextIn": 11,
            "everyDays": 30,
            "currency": "USD",
        },
        {
            "id": "sub_domain",
            "name": "Namecheap domains",
            "domain": "namecheap.com",
            "category": "Domains",
            "interval": "annual",
            "amounts": [3298, 3498],
            "descriptor": "NAMECHEAP.COM*RENEW",
            "status": "candidate",
            "confidence": 0.79,
            "explanation": "Two charges ~365 days apart with renewal emails.",
            "nextIn": 12,
            "everyDays": 365,
            "currency": "USD",
        },
        {
            "id": "sub_loom",
            "name": "Loom Business",
            "domain": "loom.com",
            "category": "Productivity",
            "interval": "monthly",
            "amounts": [1250, 1250, 1250, 1250, 1250, 1250],
            "descriptor": "LOOM.COM",
            "status": "candidate",
            "confidence": 0.86,
            "explanation": "Monthly cadence. No product emails other than receipts in 6 months.",
            "nextIn": 20,
            "everyDays": 30,
            "currency": "USD",
        },
        {
            "id": "sub_unknown",
            "name": "PAYPAL *DGTLSRV",
            "domain": "",
            "category": "Unknown",
            "interval": "monthly",
            "amounts": [999, 999, 999, 999],
            "descriptor": "PAYPAL *DGTLSRV 4029357733",
            "status": "candidate",
            "confidence": 0.62,
            "explanation": "Recurring PayPal charge with a generic descriptor; no matching email evidence.",
            "nextIn": 5,
            "everyDays": 30,
            "currency": "USD",
        },
        {
            "id": "sub_hetzner",
            "name": "Hetzner Cloud",
            "domain": "hetzner.com",
            "category": "Infrastructure",
            "interval": "monthly",
            "amounts": [1190, 1190, 1190, 1190],
            "descriptor": "HETZNER ONLINE GMBH",
            "status": "confirmed",
            "confidence": 0.93,
            "explanation": "Monthly EUR charges, matched to Hetzner invoice emails.",
            "nextIn": 1,
            "everyDays": 30,
            "currency": "EUR",
        },
    ]

    transactions: List[Transaction] = []
    evidence: Dict[str, List[EmailEvidence]] = {}
    subscriptions: List[Subscription] = []

    for s in seed_subs:
        cur = s["currency"]
        n = len(s["amounts"])
        sub_id = s["id"]
        evidence[sub_id] = []

        for i, amt in enumerate(s["amounts"]):
            ago = (n - i) * s["everyDays"] - (s["nextIn"] if s["nextIn"] is not None else 0) + (i % 2)
            tx = Transaction(
                id=f"tx_{sub_id}_{i}",
                connectionId="conn_bank",
                accountName="Chase Business ••4821",
                postedAt=days_ago(ago),
                amount=Money(amountMinor=-amt, currency=cur),
                descriptionRaw=s["descriptor"],
                merchantNormalized=s["name"] if s["domain"] else None,
                status="posted",
                isRecurringCandidate=True,
                subscriptionId=sub_id,
            )
            transactions.append(tx)

            if s["domain"] and sub_id != "sub_loom":
                ev = EmailEvidence(
                    id=f"ev_{sub_id}_{i}",
                    receivedAt=days_ago(ago + 0.2),
                    senderDomain=s["domain"],
                    subjectMinimized=f"Your {s['name']} receipt",
                    evidenceType="renewal" if s["interval"] == "annual" else "receipt",
                    amount=Money(amountMinor=amt, currency=cur),
                    invoiceDate=days_ago(ago),
                    extractionConfidence=0.9,
                    matchScore=0.92,
                    matchStatus="suggested" if i == n - 1 else "confirmed",
                    matchReason="Vendor domain, exact amount, and date within 1 day.",
                )
                evidence[sub_id].append(ev)

        last_amt = s["amounts"][-1]
        sub = Subscription(
            id=sub_id,
            vendorName=s["name"],
            vendorDomain=s["domain"] or None,
            category=s["category"],
            displayName=s["name"],
            status=s["status"],
            billingInterval=s["interval"],
            expectedAmount=Money(amountMinor=last_amt, currency=cur),
            monthlyEquivalent=Money(
                amountMinor=monthly_equivalent_minor(last_amt, s["interval"]), currency=cur
            ),
            estimatedNextChargeAt=days_ahead(s["nextIn"]) if s["nextIn"] is not None else None,
            detectionConfidence=s["confidence"],
            detectionExplanation=s["explanation"],
            lastDetectedAt=days_ago(0.1),
            note=None,
        )
        subscriptions.append(sub)

    # Miscellaneous noise transactions
    noise = [
        ("UBER *TRIP", 2340, 3),
        ("STAPLES 0042", 6712, 12),
        ("DELTA AIR 0062", 41200, 21),
        ("CLIENT PAYMENT - ACME CO", -350000, 30),
        ("STARBUCKS #1182", 645, 39),
    ]
    for i, (desc, amt, ago) in enumerate(noise):
        transactions.append(
            Transaction(
                id=f"tx_misc_{i}",
                connectionId="conn_bank",
                accountName="Chase Business ••4821",
                postedAt=days_ago(ago),
                amount=Money(amountMinor=-amt, currency="USD"),
                descriptionRaw=desc,
                merchantNormalized=None,
                status="pending" if i == 0 else "posted",
                isRecurringCandidate=False,
                subscriptionId=None,
            )
        )

    transactions.sort(key=lambda t: t.postedAt, reverse=True)

    findings = [
        Finding(
            id="fnd_dup",
            subscriptionId="sub_adobe",
            subscriptionName="Adobe Creative Cloud",
            findingType="possible_duplicate",
            severity="high",
            status="new",
            title="Two design suites billed in parallel",
            explanation="Adobe Creative Cloud and Figma Professional both charge monthly in the Design category. If you only use one, you could cancel the other.",
            estimatedImpact=Money(amountMinor=5999, currency="USD"),
            confidence=0.72,
            ruleVersion="dup-v1.2",
            createdAt=days_ago(2),
            updatedAt=days_ago(2),
        ),
        Finding(
            id="fnd_price_notion",
            subscriptionId="sub_notion",
            subscriptionName="Notion Plus",
            findingType="price_increase",
            severity="medium",
            status="new",
            title="Notion Plus went up 20%",
            explanation="Charged $10.00 for 3 cycles, then $12.00 for the last 3 cycles.",
            estimatedImpact=Money(amountMinor=200, currency="USD"),
            confidence=0.95,
            ruleVersion="price-v1.0",
            createdAt=days_ago(55),
            updatedAt=days_ago(55),
        ),
        Finding(
            id="fnd_price_adobe",
            subscriptionId="sub_adobe",
            subscriptionName="Adobe Creative Cloud",
            findingType="price_increase",
            severity="medium",
            status="reviewing",
            title="Adobe Creative Cloud went up 9%",
            explanation="Charged $54.99 for 3 cycles, then $59.99.",
            estimatedImpact=Money(amountMinor=500, currency="USD"),
            confidence=0.95,
            ruleVersion="price-v1.0",
            createdAt=days_ago(50),
            updatedAt=days_ago(10),
        ),
        Finding(
            id="fnd_loom",
            subscriptionId="sub_loom",
            subscriptionName="Loom Business",
            findingType="low_evidence",
            severity="medium",
            status="new",
            title="Loom may be forgotten",
            explanation="Six monthly charges with no product activity emails — only receipts. We can't see actual usage; review whether you still use it.",
            estimatedImpact=Money(amountMinor=1250, currency="USD"),
            confidence=0.55,
            ruleVersion="low-ev-v0.9",
            createdAt=days_ago(4),
            updatedAt=days_ago(4),
        ),
        Finding(
            id="fnd_renew",
            subscriptionId="sub_domain",
            subscriptionName="Namecheap domains",
            findingType="renewal_approaching",
            severity="low",
            status="new",
            title="Annual domain renewal in 12 days",
            explanation="Last renewal was $34.98. Expected renewal around the same amount.",
            estimatedImpact=Money(amountMinor=3498, currency="USD"),
            confidence=0.8,
            ruleVersion="renew-v1.0",
            createdAt=days_ago(1),
            updatedAt=days_ago(1),
        ),
        Finding(
            id="fnd_unclear",
            subscriptionId="sub_unknown",
            subscriptionName="PAYPAL *DGTLSRV",
            findingType="unclear_vendor",
            severity="high",
            status="new",
            title="Unidentified recurring PayPal charge",
            explanation="A $9.99 monthly charge through PayPal with a generic descriptor. No matching invoice found in Gmail.",
            estimatedImpact=Money(amountMinor=999, currency="USD"),
            confidence=0.62,
            ruleVersion="unclear-v1.0",
            createdAt=days_ago(6),
            updatedAt=days_ago(6),
        ),
    ]

    return {
        "user": default_user,
        "user_passwords": user_passwords,
        "workspace": default_workspace,
        "connections": connections,
        "subscriptions": subscriptions,
        "transactions": transactions,
        "evidence": evidence,
        "findings": findings,
    }
