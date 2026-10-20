from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from models import Connection
from services.bank_adapter import ConsentExpiredError, PlaidBankAdapter
from services.crypto import decrypt_token, encrypt_token


@pytest.fixture
def bank_test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    session = TestingSession()
    client = TestClient(app)

    yield client, session, engine

    session.close()
    app.dependency_overrides.clear()
    engine.dispose()


def test_aes_256_gcm_token_encryption():
    raw_token = "access-sandbox-prod-live-secret-oauth-token-99"
    encrypted = encrypt_token(raw_token)
    assert encrypted != raw_token
    assert isinstance(encrypted, str)

    decrypted = decrypt_token(encrypted)
    assert decrypted == raw_token

    # Tampering test
    tampered = encrypted[:-4] + "AAAA"
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt_token(tampered)


def test_bank_adapter_connect_and_encrypted_storage(bank_test_db):
    client, session, _ = bank_test_db

    # 1. Connect via API
    res = client.post(
        "/api/integrations/bank/connect",
        json={"publicToken": "public-sandbox-token-123", "institutionName": "Silicon Valley Bank"},
    )
    assert res.status_code == 200
    data = res.json()
    conn_id = data["id"]
    assert data["name"] == "Silicon Valley Bank"
    assert data["status"] == "connected"

    # 2. Assert token is encrypted at rest in SQLite database
    db_conn = session.get(Connection, conn_id)
    assert db_conn is not None
    assert db_conn.encrypted_access_token is not None
    assert not db_conn.encrypted_access_token.startswith("access-sandbox")

    # Decrypting matches the generated access token
    decrypted = decrypt_token(db_conn.encrypted_access_token)
    assert "access-sandbox-public-sandbox-token-123" in decrypted


def test_incremental_sync_and_cursor(bank_test_db):
    client, session, _ = bank_test_db

    connect_res = client.post(
        "/api/integrations/bank/connect",
        json={"publicToken": "public-sb-sync", "institutionName": "Chase Checking"},
    )
    conn_id = connect_res.json()["id"]

    # Initial sync
    sync1 = client.post(f"/api/integrations/bank/{conn_id}/sync")
    assert sync1.status_code == 200
    data1 = sync1.json()
    assert data1["success"] is True
    assert data1["addedCount"] == 3
    assert data1["nextCursor"] == "cursor_step_1"

    # Subsequent sync using next cursor
    sync2 = client.post(f"/api/integrations/bank/{conn_id}/sync?cursor=cursor_step_1")
    assert sync2.status_code == 200
    data2 = sync2.json()
    assert data2["success"] is True
    assert data2["nextCursor"] == "cursor_step_2"


def test_consent_expiration_handling(bank_test_db):
    client, session, _ = bank_test_db

    adapter = PlaidBankAdapter(session)
    conn_resp = adapter.connect("public-expired-test", institution_name="Mercury Bank")

    # Manually expire consent
    db_conn = session.get(Connection, conn_resp.id)
    db_conn.consent_expires_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    session.commit()

    # Attempting to sync an expired connection must raise ConsentExpiredError
    with pytest.raises(ConsentExpiredError):
        adapter.sync_transactions(conn_resp.id)

    # API returns HTTP 401
    api_res = client.post(f"/api/integrations/bank/{conn_resp.id}/sync")
    assert api_res.status_code == 401
    assert "consent has expired" in api_res.json()["detail"]


def test_webhook_handling_and_disconnect(bank_test_db):
    client, session, _ = bank_test_db

    conn_resp = client.post(
        "/api/integrations/bank/connect",
        json={"publicToken": "public-sb-wh", "institutionName": "Brex Cash"},
    ).json()
    conn_id = conn_resp["id"]

    # 1. Webhook: SYNC_UPDATES_AVAILABLE
    wh_sync = client.post(
        "/api/integrations/bank/webhook",
        json={"eventType": "SYNC_UPDATES_AVAILABLE", "connectionId": conn_id},
    )
    assert wh_sync.status_code == 200
    assert wh_sync.json()["handled"] is True

    # 2. Webhook: ITEM_LOGIN_REQUIRED
    wh_login = client.post(
        "/api/integrations/bank/webhook",
        json={"eventType": "ITEM_LOGIN_REQUIRED", "connectionId": conn_id},
    )
    assert wh_login.status_code == 200
    assert wh_login.json()["status"] == "reauthentication_required"

    # Status check confirms consent_expired
    status_res = client.get(f"/api/integrations/bank/{conn_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "consent_expired"

    # 3. Disconnect connection
    disc_res = client.post(f"/api/integrations/bank/{conn_id}/disconnect")
    assert disc_res.status_code == 200

    disc_status = client.get(f"/api/integrations/bank/{conn_id}/status").json()
    assert disc_status["status"] == "disconnected"
    assert disc_status["hasEncryptedToken"] is False
