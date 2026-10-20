from fastapi.testclient import TestClient
from main import app
from schemas import (
    BillingEvidenceResponse,
    ConnectionResponse,
    FindingResponse,
    Money,
    SubscriptionResponse,
    TransactionResponse,
)
from dependencies import (
    get_connection_repo,
    get_finding_repo,
    get_subscription_repo,
    get_transaction_repo,
)
from repositories.memory import (
    InMemoryConnectionRepository,
    InMemoryFindingRepository,
    InMemorySubscriptionRepository,
    InMemoryTransactionRepository,
)


def setup_fresh_repos():
    sub = SubscriptionResponse(
        id="sub_test_1",
        name="Test Tool",
        category="DevOps",
        status="active",
        billingInterval="monthly",
        amount=Money(amountMinor=4900, currency="USD"),
        monthlyEquivalent=Money(amountMinor=4900, currency="USD"),
        nextRenewalDate="2026-11-01",
        confidence=0.9,
        explanation="Test subscription",
        lastChargeDate="2026-10-01",
    )
    finding = FindingResponse(
        id="fnd_test_1",
        subscriptionId="sub_test_1",
        subscriptionName="Test Tool",
        type="forgotten_charge",
        severity="medium",
        status="open",
        title="Inactive tool charged",
        explanation="No activity recorded",
        potentialSavings=Money(amountMinor=4900, currency="USD"),
        createdAt="2026-10-20T10:00:00Z",
    )
    conn = ConnectionResponse(
        id="conn_test_1",
        name="Silicon Valley Bank",
        type="bank",
        provider="plaid",
        status="connected",
        lastSyncedAt="2026-10-19T10:00:00Z",
    )
    tx = TransactionResponse(
        id="tx_test_1",
        connectionId="conn_test_1",
        accountName="SVB Checking",
        date="2026-10-19",
        descriptionRaw="TEST TOOL INC",
        amount=Money(amountMinor=-4900, currency="USD"),
        status="posted",
        isRecurringCandidate=True,
    )

    sub_repo = InMemorySubscriptionRepository({"sub_test_1": sub})
    finding_repo = InMemoryFindingRepository({"fnd_test_1": finding})
    tx_repo = InMemoryTransactionRepository([tx])
    conn_repo = InMemoryConnectionRepository({"conn_test_1": conn})

    app.dependency_overrides[get_subscription_repo] = lambda: sub_repo
    app.dependency_overrides[get_finding_repo] = lambda: finding_repo
    app.dependency_overrides[get_transaction_repo] = lambda: tx_repo
    app.dependency_overrides[get_connection_repo] = lambda: conn_repo

    return sub_repo, finding_repo, tx_repo, conn_repo


def test_list_findings_and_filter_by_decision():
    setup_fresh_repos()
    client = TestClient(app)

    # All findings
    res = client.get("/api/findings")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["id"] == "fnd_test_1"

    # Filter pending / open
    res_pending = client.get("/api/findings?user_decision=pending")
    assert res_pending.status_code == 200
    assert len(res_pending.json()) == 1

    # Filter non-existent decision
    res_confirmed = client.get("/api/findings?user_decision=confirmed_waste")
    assert res_confirmed.status_code == 200
    assert len(res_confirmed.json()) == 0


def test_apply_finding_action_lifecycle():
    setup_fresh_repos()
    client = TestClient(app)

    # 1. Action: confirmed_waste
    payload = {
        "decision": "confirmed_waste",
        "note": "We decommissioned this server last month",
    }
    res = client.post("/api/findings/fnd_test_1/action", json=payload)
    assert res.status_code == 200
    item = res.json()
    assert item["status"] == "confirmed_waste"
    assert item["decision"] == "confirmed_waste"
    assert item["decisionNote"] == "We decommissioned this server last month"
    assert item["confirmedSavings"]["amountMinor"] == 4900

    # 2. Check overview reflects confirmed savings
    overview_res = client.get("/api/overview")
    assert overview_res.status_code == 200
    overview_data = overview_res.json()
    assert overview_data["confirmedSavings"]["amountMinor"] == 4900
    assert overview_data["openFindingsCount"] == 0

    # 3. Action on invalid finding gives 404
    res_404 = client.post("/api/findings/invalid_id/action", json=payload)
    assert res_404.status_code == 404


def test_connections_sync_and_disconnect():
    setup_fresh_repos()
    client = TestClient(app)

    # 1. List connections
    res = client.get("/api/connections")
    assert res.status_code == 200
    conns = res.json()
    assert len(conns) == 1
    assert conns[0]["status"] == "connected"

    # 2. Trigger sync
    sync_res = client.post("/api/connections/sync", json={"connectionId": "conn_test_1"})
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["status"] == "synced"
    assert "syncedAt" in sync_data

    # Check subscriptions and findings populated from pipeline
    subs_res = client.get("/api/subscriptions")
    assert subs_res.status_code == 200
    assert len(subs_res.json()) >= 1

    findings_res = client.get("/api/findings")
    assert findings_res.status_code == 200
    assert len(findings_res.json()) >= 1

    # 3. Disconnect connection
    disc_res = client.post("/api/connections/conn_test_1/disconnect", json={"deleteData": False})
    assert disc_res.status_code == 200
    assert disc_res.json() == {"success": True}

    # Verify status changed
    updated_conns = client.get("/api/connections").json()
    assert updated_conns[0]["status"] == "disconnected"


def test_purge_user_data_cleanliness():
    setup_fresh_repos()
    client = TestClient(app)

    # Ensure data exists prior to deletion
    assert len(client.get("/api/subscriptions").json()) >= 1
    assert len(client.get("/api/findings").json()) >= 1

    # Purge user data
    del_res = client.delete("/api/user/data")
    assert del_res.status_code == 204

    # Repositories must be completely clean
    assert len(client.get("/api/subscriptions").json()) == 0
    assert len(client.get("/api/findings").json()) == 0

    # App overrides cleanup
    app.dependency_overrides.clear()
