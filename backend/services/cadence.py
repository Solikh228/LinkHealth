from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from schemas import (
    BillingEvidenceResponse,
    Money,
    SubscriptionResponse,
    TransactionResponse,
)
from .normalizer import is_non_subscription_transaction, normalize_merchant


def parse_date(d_str: str) -> datetime:
    try:
        return datetime.strptime(d_str, "%Y-%m-%d")
    except ValueError:
        return datetime.fromisoformat(d_str.replace("Z", "+00:00")).replace(tzinfo=None)


def detect_cadence_and_intervals(dates: List[datetime]) -> Tuple[str, Optional[float], str]:
    """
    Evaluates transaction intervals and determines regularity.
    Returns: (cadence, average_days, cadence_explanation)
    """
    if len(dates) < 2:
        return "irregular", None, "Only 1 historical charge found; recurrence cannot be proven yet."

    dates_sorted = sorted(dates)
    diffs = [(dates_sorted[i] - dates_sorted[i - 1]).days for i in range(1, len(dates_sorted))]
    avg_diff = sum(diffs) / len(diffs)

    # Weekly: 6 - 8 days
    if 6 <= avg_diff <= 8:
        return "weekly", avg_diff, f"Charges recur every ~{round(avg_diff)} days (weekly cadence)."
    # Monthly: 26 - 35 days
    elif 26 <= avg_diff <= 35:
        return "monthly", avg_diff, f"Charges recur every ~{round(avg_diff)} days (consistent monthly cadence)."
    # Quarterly: 80 - 100 days
    elif 80 <= avg_diff <= 100:
        return "quarterly", avg_diff, f"Charges recur quarterly (~{round(avg_diff)} days apart)."
    # Annual: 350 - 380 days
    elif 350 <= avg_diff <= 380:
        return "annual", avg_diff, f"Charges recur annually (~{round(avg_diff)} days apart)."
    else:
        return "irregular", avg_diff, f"Irregular charge intervals (~{round(avg_diff)} days variance)."


def calculate_monthly_equivalent(amount_minor: int, cadence: str) -> int:
    if cadence == "weekly":
        return round(amount_minor * 52 / 12)
    elif cadence == "quarterly":
        return round(amount_minor / 3)
    elif cadence == "annual":
        return round(amount_minor / 12)
    return amount_minor


def detect_subscriptions(
    transactions: List[TransactionResponse],
    evidence_list: Optional[List[BillingEvidenceResponse]] = None,
) -> List[SubscriptionResponse]:
    """
    Groups transactions by normalized merchant, analyzes cadence, cross-references email evidence,
    and returns detected subscriptions with explainable confidence and next charge dates.
    """
    # 1. Filter out transfers, payroll, and noise
    valid_txs = [
        t for t in transactions
        if not is_non_subscription_transaction(t.descriptionRaw)
    ]

    # 2. Group by normalized vendor
    groups: Dict[str, List[TransactionResponse]] = {}
    vendor_meta: Dict[str, Tuple[str, Optional[str], Optional[str]]] = {}

    for t in valid_txs:
        name, domain, category = normalize_merchant(t.descriptionRaw)
        key = domain or name.lower()
        if key not in groups:
            groups[key] = []
            vendor_meta[key] = (name, domain, category)
        groups[key].append(t)

    evidence_by_domain: Dict[str, List[BillingEvidenceResponse]] = {}
    if evidence_list:
        for ev in evidence_list:
            dom = ev.senderDomain.lower()
            if dom not in evidence_by_domain:
                evidence_by_domain[dom] = []
            evidence_by_domain[dom].append(ev)

    detected: List[SubscriptionResponse] = []

    for key, tx_list in groups.items():
        # Require at least 2 charges or 1 charge with strong email evidence to be considered a subscription
        name, domain, category = vendor_meta[key]
        matching_evidence = evidence_by_domain.get(domain.lower(), []) if domain else []

        if len(tx_list) < 2 and not matching_evidence:
            continue

        # Sort transactions chronologically
        tx_list_sorted = sorted(tx_list, key=lambda x: parse_date(x.date))
        dates = [parse_date(t.date) for t in tx_list_sorted]
        cadence, avg_diff, cadence_reason = detect_cadence_and_intervals(dates)

        # Compute amount
        latest_tx = tx_list_sorted[-1]
        amount_minor = abs(latest_tx.amount.amountMinor)
        currency = latest_tx.amount.currency
        monthly_equiv = calculate_monthly_equivalent(amount_minor, cadence)

        # Estimate next charge date
        last_date = dates[-1]
        next_date: Optional[str] = None
        if cadence == "weekly":
            next_date = (last_date + timedelta(days=7)).strftime("%Y-%m-%d")
        elif cadence == "monthly":
            next_date = (last_date + timedelta(days=30)).strftime("%Y-%m-%d")
        elif cadence == "quarterly":
            next_date = (last_date + timedelta(days=90)).strftime("%Y-%m-%d")
        elif cadence == "annual":
            next_date = (last_date + timedelta(days=365)).strftime("%Y-%m-%d")

        # Confidence calculation
        confidence = 0.50
        reasons = [cadence_reason]

        if len(tx_list) >= 3:
            confidence += 0.25
            reasons.append(f"{len(tx_list)} consecutive statement charges detected.")
        elif len(tx_list) >= 2:
            confidence += 0.15
            reasons.append("2 recurring statement charges detected.")

        if matching_evidence:
            confidence += 0.20
            reasons.append(f"Matched {len(matching_evidence)} billing receipt emails from {domain}.")

        # Check amount consistency
        amounts = [abs(t.amount.amountMinor) for t in tx_list]
        if len(set(amounts)) == 1:
            confidence += 0.05
            reasons.append("Charge amounts are strictly identical across cycles.")
        else:
            reasons.append("Minor amount variance observed across cycles.")

        confidence = min(0.99, max(0.10, confidence))

        sub_id = f"sub_{key.replace('.', '_')}"
        sub = SubscriptionResponse(
            id=sub_id,
            name=name,
            vendorDomain=domain,
            category=category or "Other",
            status="active" if confidence >= 0.85 else "candidate",
            billingInterval=cadence,
            amount=Money(amountMinor=amount_minor, currency=currency),
            monthlyEquivalent=Money(amountMinor=monthly_equiv, currency=currency),
            nextRenewalDate=next_date,
            confidence=round(confidence, 2),
            explanation=" ".join(reasons),
            lastChargeDate=last_date.strftime("%Y-%m-%d"),
            transactions=tx_list_sorted,
            evidence=matching_evidence,
        )
        detected.append(sub)

    return detected
