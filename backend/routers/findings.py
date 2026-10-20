from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies import get_finding_repo
from repositories.base import FindingRepository
from schemas import FindingActionRequest, FindingResponse

router = APIRouter(prefix="/api/findings", tags=["Findings"])


@router.get("", response_model=List[FindingResponse])
def list_findings(
    status: Optional[str] = Query(None),
    user_decision: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    repo: FindingRepository = Depends(get_finding_repo),
):
    findings = repo.list(status=None, finding_type=type)

    target_status = status or user_decision
    if target_status:
        # Support 'pending' as alias for 'open'
        if target_status.lower() in ("pending", "open"):
            findings = [f for f in findings if f.status in ("open", "pending")]
        else:
            findings = [
                f
                for f in findings
                if f.status == target_status or getattr(f, "decision", None) == target_status
            ]

    return findings


@router.get("/{id}", response_model=FindingResponse)
def get_finding(
    id: str,
    repo: FindingRepository = Depends(get_finding_repo),
):
    finding = repo.get_by_id(id)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )
    return finding


@router.post("/{id}/action", response_model=FindingResponse)
def apply_action(
    id: str,
    action: FindingActionRequest,
    repo: FindingRepository = Depends(get_finding_repo),
):
    updated = repo.apply_action(id, action)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )
    return updated
