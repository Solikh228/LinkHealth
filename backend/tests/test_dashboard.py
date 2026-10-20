def test_get_dashboard_summary(client, auth_headers):
    res = client.get("/dashboard/summary", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert "monthlyRecurringSpend" in data
    assert data["monthlyRecurringSpend"]["amountMinor"] > 0
    assert data["subscriptionCount"] > 0
    assert data["openFindingsCount"] > 0
    assert len(data["upcoming"]) > 0
    assert len(data["spendByCategory"]) > 0
    assert len(data["connections"]) == 2


def test_api_prefix_dashboard_summary(client, auth_headers):
    res = client.get("/api/dashboard/summary", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["subscriptionCount"] > 0
