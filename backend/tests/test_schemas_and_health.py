from fastapi.testclient import TestClient
from app.main import app
from schemas import (
    Money,
    FindingActionRequest,
    SubscriptionResponse,
    FindingResponse,
    ConnectionResponse,
    OverviewMetricsResponse,
)


def test_health_check_endpoint():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_invalid_request_payload_returns_422():
    client = TestClient(app)
    # Send invalid body to auth or findings endpoint
    response = client.post("/auth/session", json={"invalidField": 123})
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert isinstance(data["detail"], list)


def test_schemas_parity():
    # Verify Pydantic v2 schemas instantiate and validate correctly
    m = Money(amountMinor=1500, currency="USD")
    assert m.amountMinor == 1500
    assert m.currency == "USD"

    action = FindingActionRequest(decision="confirmed_waste", note="Duplicate tool")
    assert action.decision == "confirmed_waste"
    assert action.note == "Duplicate tool"
    assert action.snoozeDays == 30
