def test_list_transactions(client, auth_headers):
    res = client.get("/transactions", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] > 0
    assert len(data["items"]) > 0


def test_search_transactions_by_query(client, auth_headers):
    res = client.get("/transactions?q=FIGMA", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 6
    for item in data["items"]:
        assert "FIGMA" in item["descriptionRaw"] or "Figma" in (item["merchantNormalized"] or "")


def test_transactions_pagination(client, auth_headers):
    res = client.get("/transactions?page=1&pageSize=5", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) == 5
    assert data["page"] == 1
    assert data["pageSize"] == 5
    assert data["hasMore"] is True
