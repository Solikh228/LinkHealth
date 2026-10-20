from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import Connection
from schemas import ConnectionResponse
from services.bank_adapter import ConsentExpiredError, PlaidBankAdapter
from services.cadence import detect_subscriptions
from services.waste_detector import generate_waste_findings

router = APIRouter(prefix="/api/integrations/bank", tags=["Bank Integrations"])


class ConnectBankRequest(BaseModel):
    publicToken: str
    institutionName: Optional[str] = "Plaid Sandbox Bank"
    userId: Optional[str] = None


class WebhookPayload(BaseModel):
    eventType: str
    connectionId: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@router.post("/connect", response_model=ConnectionResponse)
def connect_bank(
    payload: ConnectBankRequest,
    db: Session = Depends(get_db),
):
    adapter = PlaidBankAdapter(db)
    return adapter.connect(
        public_token=payload.publicToken,
        user_id=payload.userId,
        institution_name=payload.institutionName,
    )


@router.post("/{connection_id}/sync")
def sync_bank_transactions(
    connection_id: str,
    cursor: Optional[str] = None,
    db: Session = Depends(get_db),
):
    adapter = PlaidBankAdapter(db)
    try:
        result = adapter.sync_transactions(connection_id=connection_id, cursor=cursor)
    except ConsentExpiredError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    # Trigger detection engine for any added transactions
    from dependencies import get_finding_repo, get_subscription_repo, get_transaction_repo
    sub_repo = get_subscription_repo(db)
    finding_repo = get_finding_repo(db)
    tx_repo = get_transaction_repo(db)

    all_txs = tx_repo.list(connection_id=connection_id, limit=5000)
    detected_subs = detect_subscriptions(all_txs)
    for s in detected_subs:
        sub_repo.add(s)

    all_subs = sub_repo.list(limit=500)
    findings = generate_waste_findings(subscriptions=all_subs, transactions=all_txs)
    for f in findings:
        finding_repo.add(f)

    return {
        "success": True,
        "addedCount": len(result.added),
        "nextCursor": result.next_cursor,
        "hasMore": result.has_more,
        "detectedSubscriptions": len(detected_subs),
        "detectedFindings": len(findings),
    }


@router.post("/{connection_id}/disconnect")
def disconnect_bank(
    connection_id: str,
    db: Session = Depends(get_db),
):
    adapter = PlaidBankAdapter(db)
    success = adapter.disconnect(connection_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {connection_id} not found",
        )
    return {"success": True, "status": "disconnected"}


@router.post("/webhook")
def bank_webhook(
    payload: WebhookPayload,
    db: Session = Depends(get_db),
):
    adapter = PlaidBankAdapter(db)
    data = payload.data or {}
    data["connection_id"] = payload.connectionId
    return adapter.handle_webhook(payload.eventType, data)


@router.get("/{connection_id}/status")
def get_bank_status(
    connection_id: str,
    db: Session = Depends(get_db),
):
    conn = db.get(Connection, connection_id)
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {connection_id} not found",
        )
    return {
        "id": conn.id,
        "name": conn.name,
        "status": conn.status,
        "lastSyncedAt": conn.last_synced_at,
        "consentExpiresAt": conn.consent_expires_at,
        "hasEncryptedToken": bool(conn.encrypted_access_token),
    }
