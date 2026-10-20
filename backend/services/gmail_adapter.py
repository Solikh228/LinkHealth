import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
import os
import re
import secrets
from typing import Any, Dict, List, Optional
import urllib.parse
import uuid

import httpx
from sqlalchemy import or_
from sqlalchemy.orm import Session

from models import BillingEvidence, Connection, Subscription
from schemas import ConnectionResponse
from services.crypto import decrypt_token, encrypt_token

# Google OAuth & Gmail Restricted Scope & Query definitions
GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
GMAIL_BILLING_QUERY = "has:attachment (invoice OR receipt OR subscription OR renewal OR billing)"

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


@dataclass
class ExtractedBillingMetadata:
    id: str
    sender_domain: str
    vendor_name: str
    subject: str
    received_at: str
    amount_minor: Optional[int] = None
    currency: Optional[str] = "USD"
    invoice_date: Optional[str] = None
    confidence: float = 0.95
    snippet: Optional[str] = None


@dataclass
class GmailSyncResult:
    evidence: List[ExtractedBillingMetadata] = field(default_factory=list)
    added_count: int = 0
    next_cursor: Optional[str] = None
    has_more: bool = False


def extract_domain_from_email(from_header: str) -> str:
    """Extracts sender domain from 'From' header (e.g. 'GitHub <support@github.com>' -> 'github.com')."""
    match = re.search(r"@([\w\.-]+\.[a-zA-Z]{2,})", from_header)
    if match:
        return match.group(1).lower()
    return "unknown.com"


def extract_vendor_from_sender(from_header: str, domain: str) -> str:
    """Derives vendor name from display name or domain."""
    name_match = re.match(r"^([^<]+)<", from_header.strip())
    if name_match:
        name = name_match.group(1).strip().strip('"').strip("'")
        if name and len(name) > 1:
            return name
    parts = domain.split(".")
    if len(parts) >= 2:
        return parts[-2].capitalize()
    return domain.capitalize()


def extract_amount_and_currency(text: str) -> tuple[Optional[int], Optional[str]]:
    """Extracts currency and minor amount from subject or snippet."""
    # Matches patterns like $21.00, €15.50, £10, 21.00 USD
    patterns = [
        (r"\$([0-9]+(?:\.[0-9]{2})?)", "USD"),
        (r"€([0-9]+(?:\.[0-9]{2})?)", "EUR"),
        (r"£([0-9]+(?:\.[0-9]{2})?)", "GBP"),
        (r"([0-9]+(?:\.[0-9]{2})?)\s*(?:USD)", "USD"),
        (r"([0-9]+(?:\.[0-9]{2})?)\s*(?:EUR)", "EUR"),
        (r"([0-9]+(?:\.[0-9]{2})?)\s*(?:GBP)", "GBP"),
    ]
    for pattern, curr in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            return int(round(val * 100)), curr
    return None, None


class GmailAdapter:
    """
    Adapter for Google OAuth 2.0 flow and restricted-scope Gmail billing metadata sync.
    Adheres strictly to the Google API Services User Data Policy:
    - Requests only 'gmail.readonly'
    - Executes restricted search query 'has:attachment (invoice OR receipt OR subscription OR renewal OR billing)'
    - Retains only minimal metadata (vendor, amount, date), avoiding raw email body retention
    - AES-256-GCM token encryption at rest
    - Immediate data purge on disconnect
    """

    def __init__(self, session: Session):
        self.session = session
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv(
            "GOOGLE_REDIRECT_URI", "http://localhost:5173/integrations/callback"
        )
        self.is_live = bool(
            self.client_id
            and self.client_secret
            and "mock" not in self.client_id.lower()
        )

    def get_authorization_url(
        self,
        state: Optional[str] = None,
        redirect_uri: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generates Google OAuth 2.0 consent URL requesting strictly the minimal
        restricted scope 'https://www.googleapis.com/auth/gmail.readonly'.
        """
        state = state or secrets.token_urlsafe(16)
        redirect = redirect_uri or self.redirect_uri
        params = {
            "client_id": self.client_id or "mock-google-client-id.apps.googleusercontent.com",
            "redirect_uri": redirect,
            "response_type": "code",
            "scope": GMAIL_READONLY_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        auth_url = f"{GOOGLE_AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"
        return {
            "authUrl": auth_url,
            "state": state,
            "scope": GMAIL_READONLY_SCOPE,
        }

    def exchange_code(
        self,
        code: str,
        redirect_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Exchanges authorization code for access and refresh tokens.
        In mock/testing mode, deterministically returns verified tokens.
        """
        redirect = redirect_uri or self.redirect_uri
        if self.is_live and not code.startswith("mock_"):
            try:
                resp = httpx.post(
                    GOOGLE_TOKEN_ENDPOINT,
                    data={
                        "code": code,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uri": redirect,
                        "grant_type": "authorization_code",
                    },
                    timeout=10.0,
                )
                resp.raise_for_status()
                token_data = resp.json()
                return token_data
            except Exception as e:
                raise ValueError(f"Failed to exchange Google OAuth code: {str(e)}")

        # Deterministic Mock Token response
        return {
            "access_token": f"ya29.mock-google-access-{uuid.uuid4().hex[:12]}",
            "refresh_token": f"1//mock-google-refresh-{uuid.uuid4().hex[:12]}",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": GMAIL_READONLY_SCOPE,
            "email": "alex@studio.dev",
        }

    def connect(
        self,
        code: str,
        user_id: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        account_email: Optional[str] = None,
    ) -> ConnectionResponse:
        """
        Exchanges code, encrypts tokens at rest with AES-256-GCM, and persists Connection.
        """
        token_data = self.exchange_code(code, redirect_uri=redirect_uri)
        email = account_email or token_data.get("email") or "alex@studio.dev"

        # Encrypt tokens at rest using AES-256-GCM
        enc_access = encrypt_token(token_data.get("access_token", ""))
        enc_refresh = encrypt_token(token_data.get("refresh_token", ""))

        conn_id = f"conn_gmail_{uuid.uuid4().hex[:10]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = Connection(
            id=conn_id,
            user_id=user_id,
            name=f"Gmail ({email})",
            type="email",
            provider="gmail",
            status="connected",
            encrypted_access_token=enc_access,
            encrypted_refresh_token=enc_refresh,
            scopes_granted=GMAIL_READONLY_SCOPE,
            last_synced_at=now_iso,
        )
        self.session.add(conn)
        self.session.commit()
        self.session.refresh(conn)

        return ConnectionResponse(
            id=conn.id,
            name=conn.name,
            type=conn.type,  # type: ignore
            provider=conn.provider,  # type: ignore
            status=conn.status,  # type: ignore
            lastSyncedAt=conn.last_synced_at,
        )

    def sync_billing_emails(
        self,
        connection_id: str,
        cursor: Optional[str] = None,
    ) -> GmailSyncResult:
        """
        Executes restricted search targeting only billing-related emails.
        Extracts only minimal metadata (vendor, amount, date), avoiding raw email body retention.
        """
        conn = self.session.get(Connection, connection_id)
        if not conn:
            raise ValueError(f"Connection {connection_id} not found")
        if conn.status == "disconnected":
            raise ValueError(f"Connection {connection_id} is disconnected")

        # Verify access token can be decrypted
        if conn.encrypted_access_token:
            raw_token = decrypt_token(conn.encrypted_access_token)
        else:
            raise ValueError("No access token available for this connection")

        raw_messages: List[Dict[str, Any]] = []

        if self.is_live and not raw_token.startswith("ya29.mock"):
            # Live Gmail API integration using format="metadata"
            headers = {"Authorization": f"Bearer {raw_token}"}
            query = GMAIL_BILLING_QUERY
            if cursor:
                query += f" after:{cursor}"
            params = {"q": query, "maxResults": 25}

            resp = httpx.get(
                f"{GMAIL_API_BASE}/messages",
                headers=headers,
                params=params,
                timeout=15.0,
            )
            resp.raise_for_status()
            msg_ids = [m["id"] for m in resp.json().get("messages", [])]

            for mid in msg_ids:
                # Fetch ONLY metadata headers, NEVER raw email bodies or attachments
                m_resp = httpx.get(
                    f"{GMAIL_API_BASE}/messages/{mid}",
                    headers=headers,
                    params={
                        "format": "metadata",
                        "metadataHeaders": ["From", "Subject", "Date"],
                    },
                    timeout=10.0,
                )
                if m_resp.status_code == 200:
                    raw_messages.append(m_resp.json())
        else:
            # Deterministic mock messages satisfying the restricted billing criteria
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            raw_messages = [
                {
                    "id": f"msg_gmail_gh_{conn.id[:8]}",
                    "snippet": "Thank you for your payment to GitHub. Receipt for Team Plan $21.00.",
                    "payload": {
                        "headers": [
                            {"name": "From", "value": "GitHub <billing@github.com>"},
                            {"name": "Subject", "value": "Your receipt for GitHub Team ($21.00)"},
                            {"name": "Date", "value": "Wed, 14 Oct 2026 10:00:00 +0000"},
                        ]
                    },
                },
                {
                    "id": f"msg_gmail_slack_{conn.id[:8]}",
                    "snippet": "Slack Technologies: your monthly subscription renewed for $12.50.",
                    "payload": {
                        "headers": [
                            {"name": "From", "value": "Slack Billing <feedback@slack.com>"},
                            {"name": "Subject", "value": "Slack Pro monthly subscription receipt ($12.50)"},
                            {"name": "Date", "value": "Thu, 15 Oct 2026 09:30:00 +0000"},
                        ]
                    },
                },
                {
                    "id": f"msg_gmail_notion_{conn.id[:8]}",
                    "snippet": "Notion Plus monthly renewal notice. Invoice #NOT-29381 amount: $10.00.",
                    "payload": {
                        "headers": [
                            {"name": "From", "value": "Notion <invoices@notion.so>"},
                            {"name": "Subject", "value": "Notion invoice for workspace ($10.00)"},
                            {"name": "Date", "value": "Fri, 16 Oct 2026 12:00:00 +0000"},
                        ]
                    },
                },
                {
                    "id": f"msg_gmail_aws_{conn.id[:8]}",
                    "snippet": "Amazon Web Services invoice for billing period. Total: $45.20.",
                    "payload": {
                        "headers": [
                            {"name": "From", "value": "Amazon Web Services <no-reply@amazon.com>"},
                            {"name": "Subject", "value": "Amazon Web Services Invoice [Account: 1982] $45.20"},
                            {"name": "Date", "value": "Mon, 12 Oct 2026 08:00:00 +0000"},
                        ]
                    },
                },
            ]

        extracted_items: List[ExtractedBillingMetadata] = []
        added_count = 0

        # Query existing subscriptions to link evidence where applicable
        existing_subs = self.session.query(Subscription).all()

        for msg in raw_messages:
            msg_id = msg.get("id", str(uuid.uuid4()))
            headers_list = msg.get("payload", {}).get("headers", [])
            header_map = {h.get("name", "").lower(): h.get("value", "") for h in headers_list}

            from_hdr = header_map.get("from", "")
            subject = header_map.get("subject", "Invoice / Receipt")
            date_raw = header_map.get("date", "")
            snippet = msg.get("snippet", "")

            domain = extract_domain_from_email(from_hdr)
            vendor = extract_vendor_from_sender(from_hdr, domain)

            # Extract amount and currency from subject & snippet
            amount_minor, currency = extract_amount_and_currency(f"{subject} {snippet}")
            if not currency:
                currency = "USD"

            # Parse date
            parsed_date_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if date_raw:
                try:
                    from email.utils import parsedate_to_datetime
                    parsed_dt = parsedate_to_datetime(date_raw)
                    parsed_date_iso = parsed_dt.strftime("%Y-%m-%d")
                except Exception:
                    pass

            # Deduplication: check if provider_message_id already exists
            existing_ev = (
                self.session.query(BillingEvidence)
                .filter(
                    BillingEvidence.connection_id == conn.id,
                    BillingEvidence.provider_message_id == msg_id,
                )
                .first()
            )
            if existing_ev:
                continue

            # Attempt to link to existing subscription
            matched_sub = None
            for s in existing_subs:
                if (s.vendor_domain and s.vendor_domain.lower() == domain.lower()) or (
                    vendor.lower() in s.name.lower() or s.name.lower() in vendor.lower()
                ):
                    matched_sub = s
                    break

            ev_id = f"ev_gmail_{uuid.uuid4().hex[:10]}"
            evidence_record = BillingEvidence(
                id=ev_id,
                subscription_id=matched_sub.id if matched_sub else None,
                connection_id=conn.id,
                sender_domain=domain,
                vendor_name=vendor,
                subject=subject[:250],
                received_at=parsed_date_iso,
                confidence=0.95 if matched_sub else 0.85,
                snippet=snippet[:200] if snippet else None,
                amount_minor=amount_minor,
                currency=currency,
                invoice_date=parsed_date_iso,
                provider_message_id=msg_id,
            )
            self.session.add(evidence_record)
            added_count += 1

            meta = ExtractedBillingMetadata(
                id=ev_id,
                sender_domain=domain,
                vendor_name=vendor,
                subject=subject,
                received_at=parsed_date_iso,
                amount_minor=amount_minor,
                currency=currency,
                invoice_date=parsed_date_iso,
                confidence=0.95,
                snippet=snippet[:200] if snippet else None,
            )
            extracted_items.append(meta)

        now_iso = datetime.now(timezone.utc).isoformat()
        next_cursor = datetime.now(timezone.utc).strftime("%Y/%m/%d")
        conn.last_synced_at = now_iso
        conn.sync_cursor = next_cursor

        self.session.commit()

        return GmailSyncResult(
            evidence=extracted_items,
            added_count=added_count,
            next_cursor=next_cursor,
            has_more=False,
        )

    def disconnect(
        self,
        connection_id: str,
        purge_data: bool = True,
    ) -> Dict[str, Any]:
        """
        Disconnects Gmail integration, purges tokens at rest, and immediately deletes
        all imported billing evidence records for this connection.
        """
        conn = self.session.get(Connection, connection_id)
        if not conn:
            raise ValueError(f"Connection {connection_id} not found")

        # 1. Immediate data purge of imported email evidence
        purged_count = 0
        if purge_data:
            evidences = (
                self.session.query(BillingEvidence)
                .filter(BillingEvidence.connection_id == connection_id)
                .all()
            )
            purged_count = len(evidences)
            for ev in evidences:
                self.session.delete(ev)

        # 2. Purge encrypted tokens at rest
        conn.encrypted_access_token = None
        conn.encrypted_refresh_token = None
        conn.sync_cursor = None
        conn.status = "disconnected"

        self.session.commit()

        return {
            "success": True,
            "status": "disconnected",
            "purgedEvidenceCount": purged_count,
            "connectionId": connection_id,
        }
