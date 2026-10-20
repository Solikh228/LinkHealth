from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_overview_metrics():
    res = client.get("/api/overview")
    assert res.status_code == 200
    data = res.json()
    assert "monthlyRecurringSpend" in data
    assert "annualizedSpend" in data
    assert "activeSubscriptionCount" in data
    assert "potentialSavings" in data
    assert "confirmedSavings" in data
    assert data["activeSubscriptionCount"] >= 1


def test_list_subscriptions_filtering_and_pagination():
    res = client.get("/api/subscriptions?cadence=monthly&skip=0&limit=10")
    assert res.status_code == 200
    subs = res.json()
    assert isinstance(subs, list)
    assert len(subs) > 0
    for s in subs:
        assert s["billingInterval"] == "monthly"

    # Status filter
    res_status = client.get("/api/subscriptions?status=active")
    assert res_status.status_code == 200
    active_subs = res_status.json()
    for s in active_subs:
        assert s["status"] == "active"


def test_get_and_patch_subscription():
    res = client.get("/api/subscriptions/sub_figma")
    assert res.status_code == 200
    sub = res.json()
    assert sub["id"] == "sub_figma"
    assert sub["name"] == "Figma Professional"

    # Patch subscription
    patch_res = client.patch(
        "/api/subscriptions/sub_figma",
        json={"name": "Figma Enterprise", "status": "candidate"},
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["name"] == "Figma Enterprise"
    assert updated["status"] == "candidate"

    # Verify not found for non-existent
    err_res = client.get("/api/subscriptions/non_existent_id")
    assert err_res.status_code == 404
