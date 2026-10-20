def test_create_session_success(client):
    res = client.post("/auth/session", json={"email": "alex@studio.dev", "password": "password123"})
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["user"]["email"] == "alex@studio.dev"
    assert data["user"]["id"] == "usr_1"


def test_create_session_auto_create_new_user(client):
    res = client.post("/auth/session", json={"email": "newuser@example.com", "password": "securepass123"})
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["user"]["email"] == "newuser@example.com"


def test_protected_me_without_token_fails(client):
    res = client.get("/me")
    assert res.status_code == 401
    assert "detail" in res.json()


def test_protected_me_with_valid_token_succeeds(client, auth_headers):
    res = client.get("/me", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "alex@studio.dev"
    assert data["id"] == "usr_1"


def test_protected_workspace(client, auth_headers):
    res = client.get("/workspace", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Alex Studio"
    assert data["baseCurrency"] == "USD"


def test_delete_account(client, auth_headers):
    res = client.delete("/account", headers=auth_headers)
    assert res.status_code == 204

    # Subsequent /me with old token should fail
    res2 = client.get("/me", headers=auth_headers)
    assert res2.status_code == 401
