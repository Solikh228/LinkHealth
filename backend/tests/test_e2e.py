import os
import tempfile
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from models import Action, BillingEvidence, Connection, Finding, Subscription, Transaction
from repositories.sqlalchemy import (
    SqlAlchemyConnectionRepository,
    SqlAlchemyFindingRepository,
    SqlAlchemySubscriptionRepository,
    SqlAlchemyTransactionRepository,
)
from dependencies import (
    get_connection_repo,
    get_finding_repo,
    get_subscription_repo,
    get_transaction_repo,
)


@pytest.fixture
def e2e_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    clean_path = db_path.replace("\\", "/")
    engine = create_engine(f"sqlite:///{clean_path}")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    def override_sub_repo():
        session = TestingSessionLocal()
        return SqlAlchemySubscriptionRepository(session)

    def override_finding_repo():
        session = TestingSessionLocal()
        return SqlAlchemyFindingRepository(session)

    def override_tx_repo():
        session = TestingSessionLocal()
        return SqlAlchemyTransactionRepository(session)

    def override_conn_repo():
        session = TestingSessionLocal()
        return SqlAlchemyConnectionRepository(session)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_subscription_repo] = override_sub_repo
    app.dependency_overrides[get_finding_repo] = override_finding_repo
    app.dependency_overrides[get_transaction_repo] = override_tx_repo
    app.dependency_overrides[get_connection_repo] = override_conn_repo

    client = TestClient(app)

    yield client, TestingSessionLocal, engine

    app.dependency_overrides.clear()
    engine.dispose()
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except Exception:
        pass


def test_full_lifecycle_e2e(e2e_db):
    client, SessionLocal, engine = e2e_db

    # 1. Trigger synthetic sync and detection pipeline
    sync_res = client.post("/api/connections/sync")
    assert sync_res.status_code == 200
    assert sync_res.json()["status"] == "synced"

    # 2. Verify subscriptions detected and saved in SQLite
    subs_res = client.get("/api/subscriptions")
    assert subs_res.status_code == 200
    subs = subs_res.json()
    assert len(subs) >= 3
    sub_names = [s["name"] for s in subs]
    assert any("Figma" in name for name in sub_names)
    assert any("Adobe" in name for name in sub_names)

    # 3. Verify waste finder hypotheses generated
    findings_res = client.get("/api/findings")
    assert findings_res.status_code == 200
    findings = findings_res.json()
    assert len(findings) >= 2
    types = [f["type"] for f in findings]
    assert any(t in ("duplicate_service", "price_increase", "trial_conversion", "renewal_approaching", "forgotten_charge") for t in types)

    # Verify initial overview metrics
    overview_before = client.get("/api/overview").json()
    assert overview_before["potentialSavings"]["amountMinor"] > 0
    assert overview_before["confirmedSavings"]["amountMinor"] == 0
    assert overview_before["activeSubscriptionCount"] >= 1

    # 4. Review actions: Confirm waste on first finding
    target_fnd = findings[0]
    confirm_res = client.post(
        f"/api/findings/{target_fnd['id']}/action",
        json={"decision": "confirmed_waste", "note": "Verified duplicate subscription"},
    )
    assert confirm_res.status_code == 200
    confirmed_data = confirm_res.json()
    assert confirmed_data["status"] == "confirmed_waste"
    assert confirmed_data["confirmedSavings"]["amountMinor"] == target_fnd["potentialSavings"]["amountMinor"]

    # Verify confirmed savings reflected in overview metrics
    overview_mid = client.get("/api/overview").json()
    assert overview_mid["confirmedSavings"]["amountMinor"] == target_fnd["potentialSavings"]["amountMinor"]

    # Dismiss second finding
    if len(findings) > 1:
        dismiss_fnd = findings[1]
        dismiss_res = client.post(
            f"/api/findings/{dismiss_fnd['id']}/action",
            json={"decision": "dismissed", "note": "Active user requested retention"},
        )
        assert dismiss_res.status_code == 200
        assert dismiss_res.json()["status"] == "dismissed"

    # Pending filter excludes confirmed and dismissed findings
    pending_findings = client.get("/api/findings?user_decision=pending").json()
    pending_ids = [f["id"] for f in pending_findings]
    assert target_fnd["id"] not in pending_ids

    # 5. Permanent Data Deletion (DELETE /api/user/data)
    del_res = client.delete("/api/user/data")
    assert del_res.status_code == 204

    # Assert empty via API
    assert len(client.get("/api/subscriptions").json()) == 0
    assert len(client.get("/api/findings").json()) == 0

    # 6. Direct database inspection: assert all tables purged
    with SessionLocal() as db:
        assert db.scalar(select(Subscription)) is None
        assert db.scalar(select(Finding)) is None
        assert db.scalar(select(Transaction)) is None
        assert db.scalar(select(BillingEvidence)) is None
        assert db.scalar(select(Action)) is None

    # 7. Privacy verification: Assert no sensitive credentials or raw email bodies exist
    with SessionLocal() as db:
        # Check raw sql queries for leaks
        user_rows = db.execute(text("SELECT email, password_hash FROM users")).fetchall()
        for u in user_rows:
            # Passwords must be hashed or empty, never plaintext 'password'
            assert u[1] != "password"
            assert not u[1].startswith("plain_")

        ev_rows = db.execute(text("SELECT * FROM billing_evidence")).fetchall()
        assert len(ev_rows) == 0
