from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..auth import get_optional_user
from ..models import Finding, FindingDetail, ReviewInput, User
from ..store import store

router = APIRouter(tags=["Findings"])


@router.get("/findings", response_model=List[Finding])
def list_findings(
    status: Optional[str] = Query(None, description="Filter by status (new, reviewing, confirmed, dismissed, resolved)"),
    type: Optional[str] = Query(None, description="Filter by findingType"),
    user: User = Depends(get_optional_user),
):
    return store.list_findings(status=status, finding_type=type)


@router.get("/findings/{id}", response_model=FindingDetail)
def get_finding(id: str, user: User = Depends(get_optional_user)):
    f = store.get_finding_detail(id)
    if not f:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding '{id}' not found",
        )
    return f


@router.post("/findings/{id}/review", response_model=FindingDetail)
def review_finding(
    id: str,
    input_data: ReviewInput,
    user: User = Depends(get_optional_user),
):
    f = store.review_finding(id, input_data)
    if not f:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding '{id}' not found",
        )
    return f
