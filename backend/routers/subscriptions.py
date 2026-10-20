from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from dependencies import get_subscription_repo
from repositories.base import SubscriptionRepository
from schemas import ErrorResponse, SubscriptionResponse

router = APIRouter(prefix="/api/subscriptions", tags=["Subscriptions"])


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
    updated = repo.update(
        subscription_id=id,
        name=payload.name,
        billing_interval=payload.billingInterval,
        category=payload.category,
        status=payload.status,
        note=payload.note,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found",
        )
    return updated
