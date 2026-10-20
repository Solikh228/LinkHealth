def test_list_integrations(client, auth_headers):
    res = client.get("/integrations", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2


def test_connect_bank(client, auth_headers):
    res = client.post("/integrations/bank/connect", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["connection"]["status"] == "active"


def test_connect_gmail(client, auth_headers):
    res = client.post("/integrations/gmail/connect", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["connection"]["status"] == "active"


def test_sync_integration(client, auth_headers):
    res = client.post("/integrations/conn_bank/sync", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["lastSyncStatus"] == "success"


def test_disconnect_integration(client, auth_headers):
    res = client.post("/integrations/conn_bank/disconnect", json={"deleteData": False}, headers=auth_headers)
    assert res.status_code == 204

    # Verify status is disconnected
    res2 = client.get("/integrations", headers=auth_headers)
    conns = {c["id"]: c for c in res2.json()}
    assert conns["conn_bank"]["status"] == "disconnected"
