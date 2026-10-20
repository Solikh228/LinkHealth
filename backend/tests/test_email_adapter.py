import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from database import Base, get_db
from models import BillingEvidence, Connection
from services.crypto import decrypt_token
from services.gmail_adapter import GMAIL_BILLING_QUERY, GMAIL_READONLY_SCOPE


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


def test_google_oauth_auth_url(client):
    """Verifies that Google OAuth consent URL requests strictly minimal gmail.readonly scope."""
    res = client.get("/api/integrations/gmail/auth-url")
    assert res.status_code == 200
    data = res.json()
    assert "authUrl" in data
    assert "state" in data
    assert data["scope"] == GMAIL_READONLY_SCOPE
    assert "accounts.google.com" in data["authUrl"]
    assert "gmail.readonly" in data["authUrl"]


def test_restricted_query_definition():
    """Validates that search query targets only billing-related emails with attachments."""
    assert "has:attachment" in GMAIL_BILLING_QUERY
    for keyword in ["invoice", "receipt", "subscription", "renewal"]:
        assert keyword in GMAIL_BILLING_QUERY


def test_gmail_connect_and_token_encryption(client, db_session):
    """Verifies OAuth code exchange, AES-256-GCM token encryption at rest, and Connection creation."""
    res = client.post(
        "/api/integrations/gmail/connect",
        json={"code": "mock_auth_code_123", "accountEmail": "alex@studio.dev"},
    )
    assert res.status_code == 200
    conn_data = res.json()
    assert conn_data["type"] == "email"
    assert conn_data["provider"] == "gmail"
    assert conn_data["status"] == "connected"

    conn_id = conn_data["id"]
    db_conn = db_session.get(Connection, conn_id)
    assert db_conn is not None

    # Verify tokens are encrypted at rest with AES-256-GCM (not stored in plaintext)
    assert db_conn.encrypted_access_token is not None
    assert not db_conn.encrypted_access_token.startswith("ya29.")
    decrypted_token = decrypt_token(db_conn.encrypted_access_token)
    assert decrypted_token.startswith("ya29.")

    assert db_conn.encrypted_refresh_token is not None
    decrypted_refresh = decrypt_token(db_conn.encrypted_refresh_token)
    assert decrypted_refresh.startswith("1//")

    assert db_conn.scopes_granted == GMAIL_READONLY_SCOPE


def test_gmail_sync_minimal_metadata(client, db_session):
    """
    Verifies that Gmail sync only extracts minimal metadata (vendor, amount, date)
    and strictly avoids storing raw email bodies.
    """
    conn_res = client.post(
        "/api/integrations/gmail/connect",
        json={"code": "mock_code_test", "accountEmail": "billing@studio.dev"},
    )
    conn_id = conn_res.json()["id"]

    sync_res = client.post(f"/api/integrations/gmail/{conn_id}/sync")
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["success"] is True
    assert sync_data["addedCount"] > 0
    assert len(sync_data["evidence"]) > 0

    # Verify extracted metadata structure
    for ev in sync_data["evidence"]:
        assert ev["senderDomain"] is not None
        assert ev["vendorName"] is not None
        assert ev["receivedAt"] is not None
        assert ev["amountMinor"] is not None

    # Check database records
    ev_records = (
        db_session.query(BillingEvidence)
        .filter(BillingEvidence.connection_id == conn_id)
        .all()
    )
    assert len(ev_records) == sync_data["addedCount"]
    for record in ev_records:
        assert record.sender_domain in ["github.com", "slack.com", "notion.so", "amazon.com"]
        assert record.vendor_name is not None
        assert record.received_at is not None
        assert record.amount_minor is not None
        # Verify raw body is not retained
        assert record.snippet is None or len(record.snippet) <= 200

    # Verify status endpoint reflects evidence count
    status_res = client.get(f"/api/integrations/gmail/{conn_id}/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["evidenceCount"] == len(ev_records)
    assert status_data["tokensEncryptedAtRest"] is True
    assert status_data["scopeGranted"] == GMAIL_READONLY_SCOPE


def test_gmail_deduplication_on_repeated_sync(client, db_session):
    """Verifies that subsequent syncs with same message IDs deduplicate and don't insert duplicate evidence."""
    conn_res = client.post(
        "/api/integrations/gmail/connect",
        json={"code": "mock_code_repeat", "accountEmail": "repeat@studio.dev"},
    )
    conn_id = conn_res.json()["id"]

    first_sync = client.post(f"/api/integrations/gmail/{conn_id}/sync")
    assert first_sync.status_code == 200
    initial_count = first_sync.json()["addedCount"]

    # Second sync without new messages
    second_sync = client.post(f"/api/integrations/gmail/{conn_id}/sync")
    assert second_sync.status_code == 200
    assert second_sync.json()["addedCount"] == 0


def test_gmail_disconnect_and_immediate_data_purge(client, db_session):
    """Verifies token encryption at rest and immediate data purge on disconnect."""
    conn_res = client.post(
        "/api/integrations/gmail/connect",
        json={"code": "mock_code_purge", "accountEmail": "purge@studio.dev"},
    )
    conn_id = conn_res.json()["id"]

    # Sync evidence
    client.post(f"/api/integrations/gmail/{conn_id}/sync")
    pre_purge_count = (
        db_session.query(BillingEvidence)
        .filter(BillingEvidence.connection_id == conn_id)
        .count()
    )
    assert pre_purge_count > 0

    # Disconnect with immediate data purge
    disconnect_res = client.post(
        f"/api/integrations/gmail/{conn_id}/disconnect",
        json={"deleteData": True},
    )
    assert disconnect_res.status_code == 200
    disc_data = disconnect_res.json()
    assert disc_data["success"] is True
    assert disc_data["status"] == "disconnected"
    assert disc_data["purgedEvidenceCount"] == pre_purge_count

    # Verify all evidence for this connection has been purged from DB
    post_purge_count = (
        db_session.query(BillingEvidence)
        .filter(BillingEvidence.connection_id == conn_id)
        .count()
    )
    assert post_purge_count == 0

    # Verify tokens at rest have been purged
    db_conn = db_session.get(Connection, conn_id)
    assert db_conn.status == "disconnected"
    assert db_conn.encrypted_access_token is None
    assert db_conn.encrypted_refresh_token is None
    assert db_conn.sync_cursor is None
