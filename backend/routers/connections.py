from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from dependencies import (
    get_connection_repo,
    get_finding_repo,
    get_subscription_repo,
    get_transaction_repo,
)
from repositories.base import (
    ConnectionRepository,
    FindingRepository,
    SubscriptionRepository,
    TransactionRepository,
)
from schemas import ConnectionResponse
from services.cadence import detect_subscriptions
from services.synthetic_data import generate_synthetic_data
from services.waste_detector import generate_waste_findings

router = APIRouter(tags=["Connections & User Data"])


class SyncRequest(BaseModel):
    connectionId: Optional[str] = None


class DisconnectRequest(BaseModel):
    deleteData: Optional[bool] = False


@router.get("/api/connections", response_model=List[ConnectionResponse])
def list_connections(
    repo: ConnectionRepository = Depends(get_connection_repo),
):
    return repo.list()


@router.post("/api/connections/sync")
def sync_connections(
    payload: Optional[SyncRequest] = None,
    conn_repo: ConnectionRepository = Depends(get_connection_repo),
    sub_repo: SubscriptionRepository = Depends(get_subscription_repo),
    tx_repo: TransactionRepository = Depends(get_transaction_repo),
    finding_repo: FindingRepository = Depends(get_finding_repo),
):
    conn_id = payload.connectionId if payload else None
    conn_repo.sync(connection_id=conn_id)

    # In-process sync via synthetic data harness
    data = generate_synthetic_data()
    transactions = data.get("transactions", [])
    evidence = data.get("evidence", [])

    for tx in transactions:
        tx_repo.add(tx)

    detected_subs = detect_subscriptions(transactions, evidence)
    for sub in detected_subs:
        sub_repo.add(sub)

    # Run detection pipeline
    all_subs = sub_repo.list()
    all_txs = tx_repo.list(limit=1000)
    findings = generate_waste_findings(
        subscriptions=all_subs,
        transactions=all_txs,
        evidence_list=evidence,
    )
    for f in findings:
        finding_repo.add(f)

    now_iso = datetime.now(timezone.utc).isoformat()
    return {"status": "synced", "syncedAt": now_iso}


@router.post("/api/connections/{id}/disconnect")
def disconnect_connection(
    id: str,
    payload: Optional[DisconnectRequest] = None,
    repo: ConnectionRepository = Depends(get_connection_repo),
):
    delete_data = payload.deleteData if payload else False
    success = repo.disconnect(connection_id=id, delete_data=delete_data)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )
    return {"success": True}


@router.delete("/api/user/data", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_data(
    sub_repo: SubscriptionRepository = Depends(get_subscription_repo),
    finding_repo: FindingRepository = Depends(get_finding_repo),
    tx_repo: TransactionRepository = Depends(get_transaction_repo),
):
    sub_repo.clear()
    finding_repo.clear()
    tx_repo.clear()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
