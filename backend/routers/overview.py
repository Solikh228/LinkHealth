from fastapi import APIRouter, Depends
from dependencies import get_finding_repo, get_subscription_repo
from repositories.base import FindingRepository, SubscriptionRepository
from schemas import Money, OverviewMetricsResponse

router = APIRouter(prefix="/api/overview", tags=["Overview"])


@router.get("", response_model=OverviewMetricsResponse)
def get_overview(
    sub_repo: SubscriptionRepository = Depends(get_subscription_repo),
    finding_repo: FindingRepository = Depends(get_finding_repo),
):
    subs = sub_repo.list()
    active_subs = [s for s in subs if s.status not in ("dismissed", "cancelled")]
    monthly_spend = sum(s.monthlyEquivalent.amountMinor for s in active_subs)

    findings = finding_repo.list()
    open_findings = [f for f in findings if f.status == "open"]
    potential_savings = sum(f.potentialSavings.amountMinor for f in open_findings)

    confirmed_savings = sum(
        f.confirmedSavings.amountMinor
        for f in findings
        if f.status == "confirmed_waste" and f.confirmedSavings
    )

    upcoming_count = len([s for s in active_subs if s.billingInterval == "annual"])

    return OverviewMetricsResponse(
        monthlyRecurringSpend=Money(amountMinor=monthly_spend, currency="USD"),
        annualizedSpend=Money(amountMinor=monthly_spend * 12, currency="USD"),
        activeSubscriptionCount=len(active_subs),
        potentialSavings=Money(amountMinor=potential_savings, currency="USD"),
        confirmedSavings=Money(amountMinor=confirmed_savings, currency="USD"),
        openFindingsCount=len(open_findings),
        upcomingRenewalsCount=upcoming_count,
    )
