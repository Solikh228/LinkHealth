from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import uuid

from schemas import (
    BillingEvidenceResponse,
    FindingResponse,
    Money,
    SubscriptionResponse,
    TransactionResponse,
)


def generate_waste_findings(
    subscriptions: List[SubscriptionResponse],
    transactions: Optional[List[TransactionResponse]] = None,
    evidence_list: Optional[List[BillingEvidenceResponse]] = None,
    reference_date: Optional[datetime] = None,
) -> List[FindingResponse]:
    """
    Generates rule-based waste finder hypotheses for:
      - forgotten_charge
      - trial_conversion
      - price_increase
      - duplicate_service (possible_duplicate)
      - renewal_approaching
    Every finding phrases conclusions strictly as hypotheses with supporting evidence.
    """
    findings: List[FindingResponse] = []
    now = reference_date or datetime(2026, 10, 20, 12, 0, 0, tzinfo=timezone.utc)
    evidence_by_sub: Dict[str, List[BillingEvidenceResponse]] = {}
    if evidence_list:
        for ev in evidence_list:
            if ev.subscriptionId not in evidence_by_sub:
                evidence_by_sub[ev.subscriptionId] = []
            evidence_by_sub[ev.subscriptionId].append(ev)

    # 1. Price Increase Detection
    for sub in subscriptions:
        txs = sub.transactions or [t for t in (transactions or []) if getattr(t, "subscriptionId", None) == sub.id]
        if len(txs) >= 2:
            amounts = [abs(t.amount.amountMinor) for t in txs]
            if amounts[-1] > amounts[0]:
                increase_minor = amounts[-1] - amounts[0]
                pct = round((increase_minor / amounts[0]) * 100)
                findings.append(
                    FindingResponse(
                        id=f"fnd_price_{sub.id}",
                        subscriptionId=sub.id,
                        subscriptionName=sub.name,
                        type="price_increase",
                        severity="medium",
                        status="open",
                        title=f"{sub.name} increased by {pct}%",
                        explanation=f"Charged ${amounts[0]/100:.2f} in earlier cycles, then rose to ${amounts[-1]/100:.2f} recently.",
                        potentialSavings=Money(amountMinor=increase_minor, currency=sub.amount.currency),
                        evidence=evidence_by_sub.get(sub.id, sub.evidence),
                        createdAt=now.isoformat(),
                    )
                )

    # 2. Trial Conversion Detection
    # Look for trial ending emails or transactions marked with trial conversion
    for sub in subscriptions:
        sub_evs = evidence_by_sub.get(sub.id, sub.evidence)
        trial_ev = next((e for e in sub_evs if "trial" in e.subject.lower() or "trial" in (e.snippet or "").lower()), None)
        has_trial_tx = any("trial" in t.descriptionRaw.lower() for t in sub.transactions)

        if trial_ev or has_trial_tx:
            findings.append(
                FindingResponse(
                    id=f"fnd_trial_{sub.id}",
                    subscriptionId=sub.id,
                    subscriptionName=sub.name,
                    type="trial_conversion",
                    severity="high",
                    status="open",
                    title=f"{sub.name} trial converted to recurring billing",
                    explanation=f"A trial period concluded and converted into a recurring ${sub.amount.amountMinor/100:.2f}/mo charge. Verify ongoing necessity.",
                    potentialSavings=Money(amountMinor=sub.amount.amountMinor, currency=sub.amount.currency),
                    evidence=sub_evs,
                    createdAt=now.isoformat(),
                )
            )

    # 3. Possible Duplicate Detection
    # Two active subscriptions in the same vendor category (e.g. Design: Adobe and Figma)
    by_category: Dict[str, List[SubscriptionResponse]] = {}
    for sub in subscriptions:
        if sub.status in ("active", "candidate") and sub.category:
            by_category.setdefault(sub.category, []).append(sub)

    for cat, sub_group in by_category.items():
        if len(sub_group) >= 2:
            s1, s2 = sub_group[0], sub_group[1]
            more_expensive = s1 if s1.amount.amountMinor >= s2.amount.amountMinor else s2
            findings.append(
                FindingResponse(
                    id=f"fnd_dup_{cat.lower()}",
                    subscriptionId=more_expensive.id,
                    subscriptionName=more_expensive.name,
                    type="duplicate_service",
                    severity="high",
                    status="open",
                    title=f"Parallel {cat} tools detected ({s1.name} & {s2.name})",
                    explanation=f"Both {s1.name} and {s2.name} bill in the {cat} category. If only one tool is actively used, the other could be cancelled.",
                    potentialSavings=Money(amountMinor=more_expensive.amount.amountMinor, currency=more_expensive.amount.currency),
                    evidence=more_expensive.evidence,
                    createdAt=now.isoformat(),
                )
            )

    # 4. Renewal Approaching Detection
    # Charges scheduled within 14 days
    for sub in subscriptions:
        if sub.nextRenewalDate:
            try:
                renewal_dt = datetime.strptime(sub.nextRenewalDate, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                days_until = (renewal_dt - now).days
                if 0 <= days_until <= 14:
                    findings.append(
                        FindingResponse(
                            id=f"fnd_renewal_{sub.id}",
                            subscriptionId=sub.id,
                            subscriptionName=sub.name,
                            type="renewal_approaching",
                            severity="medium" if sub.billingInterval == "annual" else "low",
                            status="open",
                            title=f"{sub.name} renewal approaching in {days_until} days",
                            explanation=f"Expected charge of ${sub.amount.amountMinor/100:.2f} due on {sub.nextRenewalDate}. Review before auto-charge occurs.",
                            potentialSavings=Money(amountMinor=sub.amount.amountMinor, currency=sub.amount.currency),
                            evidence=evidence_by_sub.get(sub.id, sub.evidence),
                            createdAt=now.isoformat(),
                        )
                    )
            except ValueError:
                pass

    # 5. Forgotten Charge Detection
    # Subscriptions in candidate status or lacking regular email engagement
    for sub in subscriptions:
        if sub.status == "candidate" and not any(f.subscriptionId == sub.id and f.type in ("price_increase", "trial_conversion") for f in findings):
            findings.append(
                FindingResponse(
                    id=f"fnd_forgotten_{sub.id}",
                    subscriptionId=sub.id,
                    subscriptionName=sub.name,
                    type="forgotten_charge",
                    severity="medium",
                    status="open",
                    title=f"{sub.name} may be forgotten",
                    explanation=f"Recurring charges observed on statement without recent activity confirmations. Review ongoing necessity.",
                    potentialSavings=Money(amountMinor=sub.amount.amountMinor, currency=sub.amount.currency),
                    evidence=evidence_by_sub.get(sub.id, sub.evidence),
                    createdAt=now.isoformat(),
                )
            )

    return findings
