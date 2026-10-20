def test_list_subscriptions(client, auth_headers):
    res = client.get("/subscriptions", headers=auth_headers)
    assert res.status_code == 200
    subs = res.json()
    assert len(subs) == 8
    names = [s["vendorName"] for s in subs]
    assert "Figma Professional" in names
    assert "Amazon Web Services" in names


def test_get_subscription_detail(client, auth_headers):
    res = client.get("/subscriptions/sub_figma", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "sub_figma"
    assert len(data["transactions"]) == 6
    assert len(data["evidence"]) == 6


def test_get_nonexistent_subscription_returns_404(client, auth_headers):
    res = client.get("/subscriptions/sub_nonexistent", headers=auth_headers)
    assert res.status_code == 404


def test_patch_subscription(client, auth_headers):
    res = client.patch(
        "/subscriptions/sub_notion",
        json={"displayName": "Notion Team Workspace", "note": "Reviewed by Alex"},
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["displayName"] == "Notion Team Workspace"
    assert data["note"] == "Reviewed by Alex"


def test_confirm_and_dismiss_subscription(client, auth_headers):
    res = client.post("/subscriptions/sub_notion/confirm", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["status"] == "confirmed"

    res2 = client.post("/subscriptions/sub_notion/dismiss", headers=auth_headers)
    assert res2.status_code == 200
    assert res2.json()["status"] == "dismissed"
