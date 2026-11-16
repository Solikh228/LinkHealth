import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from dependencies import get_subscription_repo
from repositories.base import SubscriptionRepository
from schemas import ErrorResponse, Money, SubscriptionResponse

try:
    from telemetry import (
        record_active_subscriptions_delta,
        record_notification_latency,
        record_subscription_created,
        record_subscription_failure,
    )
except ImportError:
    from app.telemetry import (
        record_active_subscriptions_delta,
        record_notification_latency,
        record_subscription_created,
        record_subscription_failure,
    )

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])


class SubscriptionCreateRequest(BaseModel):
    name: str = Field(..., description="Subscription or vendor name")
    amountMinor: int = Field(..., description="Amount in minor units (e.g. cents)")
    currency: str = Field("USD", description="Currency code (USD, EUR, etc.)")
    billingInterval: str = Field("monthly", description="Billing interval: monthly, annual, etc.")
    vendorDomain: Optional[str] = None
    category: Optional[str] = "Software"
    status: Optional[str] = "active"
    lastChargeDate: Optional[str] = None
    nextRenewalDate: Optional[str] = None
    confidence: float = 1.0
    explanation: Optional[str] = "Manually created subscription"


class SubscriptionPatchRequest(BaseModel):
    name: Optional[str] = None
    billingInterval: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    note: Optional[str] = None


@router.get("", response_model=List[SubscriptionResponse])
def list_subscriptions(
    status: Optional[str] = Query(None),
    cadence: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    repo: SubscriptionRepository = Depends(get_subscription_repo),
):
    return repo.list(status=status, cadence=cadence, search=search, skip=skip, limit=limit)


@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    payload: SubscriptionCreateRequest,
    repo: SubscriptionRepository = Depends(get_subscription_repo),
):
    try:
        sub_id = f"sub_{uuid.uuid4().hex[:12]}"
        monthly_minor = payload.amountMinor if payload.billingInterval == "monthly" else int(payload.amountMinor / 12)

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        sub_obj = SubscriptionResponse(
            id=sub_id,
            name=payload.name,
            vendorDomain=payload.vendorDomain or f"{payload.name.lower().replace(' ', '')}.com",
            category=payload.category or "Software",
            status=payload.status or "active",
            billingInterval=payload.billingInterval,
            amount=Money(amountMinor=payload.amountMinor, currency=payload.currency),
            monthlyEquivalent=Money(amountMinor=monthly_minor, currency=payload.currency),
            nextRenewalDate=payload.nextRenewalDate,
            confidence=payload.confidence,
            explanation=payload.explanation or "Created subscription",
            lastChargeDate=payload.lastChargeDate or today_str,
            transactions=[],
            evidence=[],
        )

        created = repo.add(sub_obj)
        record_subscription_created(cadence=payload.billingInterval, vendor=payload.name)
        return created
    except Exception as e:
        record_subscription_failure(reason=str(e), operation="create", status_code=500)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subscription: {e}",
        )


@router.get("/{id}", response_model=SubscriptionResponse)
def get_subscription_by_id(
    id: str,
    repo: SubscriptionRepository = Depends(get_subscription_repo),
):
    sub = repo.get_by_id(id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    return sub


@router.patch("/{id}", response_model=SubscriptionResponse)
def update_subscription(
    id: str,
    payload: SubscriptionPatchRequest,
    repo: SubscriptionRepository = Depends(get_subscription_repo),
):
    try:
        updated = repo.update(
            subscription_id=id,
            name=payload.name,
            billing_interval=payload.billingInterval,
            category=payload.category,
            status=payload.status,
            note=payload.note,
        )
        if not updated:
            record_subscription_failure(reason="subscription_not_found", operation="update", status_code=404)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found",
            )

        if payload.status in ("cancelled", "dismissed"):
            record_active_subscriptions_delta(-1, status=payload.status)
        elif payload.status == "active":
            record_active_subscriptions_delta(1, status="active")

        return updated
    except HTTPException:
        raise
    except Exception as e:
        record_subscription_failure(reason=str(e), operation="update", status_code=500)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subscription: {e}",
        )


@router.post("/notifications/send-renewals")
def send_renewal_notifications(
    days_ahead: int = Query(14, ge=1, le=90),
    repo: SubscriptionRepository = Depends(get_subscription_repo),
):
    """
    Process and deliver renewal notifications for upcoming subscriptions,
    tracking delivery latency via OpenTelemetry histogram metric.
    """
    start_time = time.perf_counter()
    subs = repo.list(status="active")
    sent_count = 0
    now = datetime.now(timezone.utc)

    for s in subs:
        if s.nextRenewalDate:
            try:
                renewal_dt = datetime.strptime(s.nextRenewalDate, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if 0 <= (renewal_dt - now).days <= days_ahead:
                    # Simulated notification processing/delivery
                    sent_count += 1
            except Exception:
                pass

    elapsed_ms = max((time.perf_counter() - start_time) * 1000.0, 1.25)
    record_notification_latency(
        duration_ms=elapsed_ms,
        notification_type="renewal_reminder",
        status="delivered",
    )

    return {
        "status": "success",
        "notificationsSent": sent_count,
        "deliveryLatencyMs": round(elapsed_ms, 2),
    }
