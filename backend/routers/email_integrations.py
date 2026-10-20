from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import BillingEvidence, Connection
from schemas import ConnectionResponse
from services.cadence import detect_subscriptions
from services.gmail_adapter import GMAIL_READONLY_SCOPE, GmailAdapter
from services.waste_detector import generate_waste_findings

router = APIRouter(prefix="/api/integrations/gmail", tags=["Gmail Integrations"])


class ConnectGmailRequest(BaseModel):
    code: str
    accountEmail: Optional[str] = "alex@studio.dev"
    redirectUri: Optional[str] = None
    userId: Optional[str] = None


class DisconnectGmailRequest(BaseModel):
    deleteData: Optional[bool] = True


@router.get("/auth-url")
def get_gmail_auth_url(
    state: Optional[str] = None,
    redirectUri: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Returns Google OAuth 2.0 authorization URL requesting minimal restricted scope 'gmail.readonly'."""
    adapter = GmailAdapter(db)
    return adapter.get_authorization_url(state=state, redirect_uri=redirectUri)


@router.post("/connect", response_model=ConnectionResponse)
def connect_gmail(
    payload: ConnectGmailRequest,
    db: Session = Depends(get_db),
):
    """
    Exchanges Google OAuth authorization code for encrypted tokens and creates Connection.
    """
    adapter = GmailAdapter(db)
    return adapter.connect(
        code=payload.code,
        user_id=payload.userId,
        redirect_uri=payload.redirectUri,
        account_email=payload.accountEmail,
    )


@router.post("/{connection_id}/sync")
def sync_gmail(
    connection_id: str,
    cursor: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Searches billing-related emails ('has:attachment', invoice/receipt keywords),
    extracts minimal metadata without retaining email bodies, and encrypts credentials.
    """
    adapter = GmailAdapter(db)
    try:
        result = adapter.sync_billing_emails(connection_id=connection_id, cursor=cursor)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    # Cross-reference with detection engine
    from dependencies import get_finding_repo, get_subscription_repo, get_transaction_repo
    sub_repo = get_subscription_repo(db)
    finding_repo = get_finding_repo(db)
    tx_repo = get_transaction_repo(db)

    all_txs = tx_repo.list(limit=5000)
    detected_subs = detect_subscriptions(all_txs)
    for s in detected_subs:
        sub_repo.add(s)

    all_subs = sub_repo.list(limit=500)
    findings = generate_waste_findings(subscriptions=all_subs, transactions=all_txs)
    for f in findings:
        finding_repo.add(f)

    return {
        "success": True,
        "addedCount": result.added_count,
        "nextCursor": result.next_cursor,
        "hasMore": result.has_more,
        "evidence": [
            {
                "id": e.id,
                "senderDomain": e.sender_domain,
                "vendorName": e.vendor_name,
                "subject": e.subject,
                "receivedAt": e.received_at,
                "amountMinor": e.amount_minor,
                "currency": e.currency,
                "confidence": e.confidence,
            }
            for e in result.evidence
        ],
    }


@router.post("/{connection_id}/disconnect")
def disconnect_gmail(
    connection_id: str,
    payload: Optional[DisconnectGmailRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Disconnects Gmail integration, purges tokens at rest, and immediately deletes
    all imported billing evidence records for this connection.
    """
    adapter = GmailAdapter(db)
    purge_data = payload.deleteData if payload else True
    try:
        return adapter.disconnect(connection_id=connection_id, purge_data=purge_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{connection_id}/status")
def get_gmail_status(
    connection_id: str,
    db: Session = Depends(get_db),
):
    """Returns integration health, scope compliance, encryption status, and evidence count."""
    conn = db.get(Connection, connection_id)
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connection {connection_id} not found",
        )

    evidence_count = (
        db.query(BillingEvidence)
        .filter(BillingEvidence.connection_id == connection_id)
        .count()
    )

    return {
        "id": conn.id,
        "name": conn.name,
        "status": conn.status,
        "provider": conn.provider,
        "scopeGranted": conn.scopes_granted or GMAIL_READONLY_SCOPE,
        "tokensEncryptedAtRest": bool(conn.encrypted_access_token),
        "evidenceCount": evidence_count,
        "lastSyncedAt": conn.last_synced_at,
    }
