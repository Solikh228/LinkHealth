from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ..auth import get_optional_user
from ..models import Subscription, SubscriptionDetail, SubscriptionPatch, User
from ..store import store

try:
    from telemetry import (
        record_active_subscriptions_delta,
        record_subscription_created,
        record_subscription_failure,
    )
except ImportError:
    from app.telemetry import (
        record_active_subscriptions_delta,
        record_subscription_created,
        record_subscription_failure,
    )

router = APIRouter(tags=["Subscriptions"])


@router.get("/subscriptions", response_model=List[Subscription])
def list_subscriptions(user: User = Depends(get_optional_user)):
    return store.list_subscriptions()


@router.get("/subscriptions/{id}", response_model=SubscriptionDetail)
def get_subscription(id: str, user: User = Depends(get_optional_user)):
    sub = store.get_subscription_detail(id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription '{id}' not found",
        )
    return sub


@router.patch("/subscriptions/{id}", response_model=Subscription)
def update_subscription(
    id: str,
    patch: SubscriptionPatch,
    user: User = Depends(get_optional_user),
):
    try:
        sub = store.update_subscription(id, patch)
        if not sub:
            record_subscription_failure(reason="subscription_not_found", operation="update", status_code=404)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription '{id}' not found",
            )
        if patch.status in ("cancelled", "dismissed"):
            record_active_subscriptions_delta(-1, status=patch.status)
        elif patch.status == "active":
            record_active_subscriptions_delta(1, status="active")
        return sub
    except HTTPException:
        raise
    except Exception as e:
        record_subscription_failure(reason=str(e), operation="update", status_code=500)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update subscription: {e}",
        )


@router.post("/subscriptions/{id}/confirm", response_model=Subscription)
def confirm_subscription(id: str, user: User = Depends(get_optional_user)):
    sub = store.confirm_subscription(id)
    if not sub:
        record_subscription_failure(reason="confirm_not_found", operation="confirm", status_code=404)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription '{id}' not found",
        )
    record_active_subscriptions_delta(1, status="confirmed")
    return sub


@router.post("/subscriptions/{id}/dismiss", response_model=Subscription)
def dismiss_subscription(id: str, user: User = Depends(get_optional_user)):
    sub = store.dismiss_subscription(id)
    if not sub:
        record_subscription_failure(reason="dismiss_not_found", operation="dismiss", status_code=404)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription '{id}' not found",
        )
    record_active_subscriptions_delta(-1, status="dismissed")
    return sub
