from typing import Optional
from fastapi import APIRouter, Depends, Query
from ..auth import get_optional_user
from ..models import Paginated, Transaction, User
from ..store import store

router = APIRouter(tags=["Transactions"])


@router.get("/transactions", response_model=Paginated[Transaction])
def list_transactions(
    q: Optional[str] = Query(None, description="Search term for merchant or description"),
    status: Optional[str] = Query(None, description="Transaction status filter"),
    subscriptionId: Optional[str] = Query(None, description="Filter by linked subscription"),
    page: int = Query(1, ge=1, description="Page number"),
    pageSize: int = Query(50, ge=1, le=100, description="Items per page"),
    user: User = Depends(get_optional_user),
):
    return store.list_transactions(
        q=q,
        status=status,
        subscription_id=subscriptionId,
        page=page,
        page_size=pageSize,
    )
