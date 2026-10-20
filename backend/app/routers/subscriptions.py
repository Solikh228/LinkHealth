from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from ..auth import get_optional_user
from ..models import Subscription, SubscriptionDetail, SubscriptionPatch, User
from ..store import store

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
    sub = store.update_subscription(id, patch)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription '{id}' not found",
        )
    return sub


@router.post("/subscriptions/{id}/confirm", response_model=Subscription)
def confirm_subscription(id: str, user: User = Depends(get_optional_user)):
    sub = store.confirm_subscription(id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription '{id}' not found",
        )
    return sub


@router.post("/subscriptions/{id}/dismiss", response_model=Subscription)
def dismiss_subscription(id: str, user: User = Depends(get_optional_user)):
    sub = store.dismiss_subscription(id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription '{id}' not found",
        )
    return sub
