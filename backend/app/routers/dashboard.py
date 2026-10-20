from fastapi import APIRouter, Depends
from ..auth import get_optional_user
from ..models import DashboardSummary, User
from ..store import store

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/summary", response_model=DashboardSummary)
def get_dashboard_summary(user: User = Depends(get_optional_user)):
    return store.get_dashboard_summary()
