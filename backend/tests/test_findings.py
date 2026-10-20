def test_list_findings(client, auth_headers):
    res = client.get("/findings", headers=auth_headers)
    assert res.status_code == 200
    findings = res.json()
    assert len(findings) == 6


def test_filter_findings_by_status(client, auth_headers):
    res = client.get("/findings?status=reviewing", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["id"] == "fnd_price_adobe"


def test_get_finding_detail(client, auth_headers):
    res = client.get("/findings/fnd_dup", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "fnd_dup"
    assert "evidence" in data
    assert len(data["evidence"]) > 0


def test_review_finding(client, auth_headers):
    res = client.post(
        "/findings/fnd_dup/review",
        json={
            "decision": "confirm",
            "note": "We cancelled Adobe CC in favor of Figma",
            "estimatedSavings": {"amountMinor": 5999, "currency": "USD"},
        },
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "confirmed"
    assert len(data["reviews"]) == 1
    assert data["reviews"][0]["decision"] == "confirm"
    assert data["reviews"][0]["estimatedSavings"]["amountMinor"] == 5999
