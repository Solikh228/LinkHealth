import csv
import io
from fastapi.testclient import TestClient
from main import app
from schemas import FindingActionRequest, FindingResponse, Money, SubscriptionResponse
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


def setup_fresh_test_environment():
    sub_repo = InMemorySubscriptionRepository({})
    finding_repo = InMemoryFindingRepository({})
    tx_repo = InMemoryTransactionRepository([])
    conn_repo = InMemoryConnectionRepository({})

    app.dependency_overrides[get_subscription_repo] = lambda: sub_repo
    app.dependency_overrides[get_finding_repo] = lambda: finding_repo
    app.dependency_overrides[get_transaction_repo] = lambda: tx_repo
    app.dependency_overrides[get_connection_repo] = lambda: conn_repo

    return sub_repo, finding_repo, tx_repo, conn_repo


def test_csv_import_json_payload():
    setup_fresh_test_environment()
    client = TestClient(app)

    csv_data = """Date,Merchant,Amount,Currency
2026-08-01,FIGMA.COM,15.00,USD
2026-09-01,FIGMA.COM,15.00,USD
2026-10-01,FIGMA.COM,15.00,USD
2026-08-15,AWS CLOUD,50.00,USD
2026-09-15,AWS CLOUD,75.00,USD
2026-10-15,AWS CLOUD,120.00,USD
"""
    res = client.post(
        "/api/statements/import-csv",
        json={"csvContent": csv_data},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["importedTransactions"] == 6

    # Verify subscriptions detected from CSV
    subs_res = client.get("/api/subscriptions")
    assert subs_res.status_code == 200
    subs = subs_res.json()
    assert len(subs) >= 1

    # Verify findings generated from imported statement
    findings_res = client.get("/api/findings")
    assert findings_res.status_code == 200
    assert len(findings_res.json()) >= 1


def test_csv_upload_multipart_file():
    setup_fresh_test_environment()
    client = TestClient(app)

    csv_buffer = io.BytesIO(
        b"Transaction Date,Description,Total\n"
        b"2026-08-10,NOTION LABS,10.00\n"
        b"2026-09-10,NOTION LABS,10.00\n"
        b"2026-10-10,NOTION LABS,10.00\n"
    )

    files = {"file": ("statement.csv", csv_buffer, "text/csv")}
    data = {
        "date_column": "Transaction Date",
        "merchant_column": "Description",
        "amount_column": "Total",
    }
    res = client.post("/api/statements/upload-csv", files=files, data=data)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["importedTransactions"] == 3


def test_csv_export_savings_report():
    sub_repo, finding_repo, _, _ = setup_fresh_test_environment()
    client = TestClient(app)

    # Seed a finding
    fnd = FindingResponse(
        id="fnd_export_1",
        subscriptionId="sub_1",
        subscriptionName="Redundant Tool",
        type="duplicate_service",
        severity="high",
        status="confirmed_waste",
        title="Duplicate SaaS",
        explanation="Two tools with overlapping functionality",
        potentialSavings=Money(amountMinor=3500, currency="USD"),
        confirmedSavings=Money(amountMinor=3500, currency="USD"),
        createdAt="2026-10-20T00:00:00Z",
        decision="confirmed_waste",
        decisionNote="Decommissioned seat",
    )
    finding_repo.add(fnd)

    res = client.get("/api/reports/savings-csv")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=" in res.headers["content-disposition"]

    content = res.text
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) == 2  # Header + 1 finding
    assert rows[0][0] == "Finding ID"
    assert rows[1][0] == "fnd_export_1"
    assert rows[1][2] == "Redundant Tool"
    assert rows[1][8] == "35.00"  # Potential
    assert rows[1][9] == "35.00"  # Confirmed


def test_csv_invalid_columns():
    setup_fresh_test_environment()
    client = TestClient(app)

    res = client.post(
        "/api/statements/import-csv",
        json={"csvContent": "ColA,ColB\n1,2\n"},
    )
    assert res.status_code == 400
    assert "Missing required columns" in res.json()["detail"]
