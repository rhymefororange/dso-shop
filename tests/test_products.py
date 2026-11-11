def test_list_products(client):
    resp = client.get("/api/products")
    assert resp.status_code == 200
    items = resp.get_json()["items"]
    assert len(items) == 12
    assert {"id", "name", "price", "stock"} <= set(items[0])


def test_pagination(client):
    resp = client.get("/api/products?limit=5&offset=10")
    assert [p["id"] for p in resp.get_json()["items"]] == [11, 12]


def test_pagination_rejects_non_integers(client):
    assert client.get("/api/products?limit=abc").status_code == 400


def test_product_detail(client):
    resp = client.get("/api/products/1")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "DevSecOps Mug"
    assert client.get("/api/products/9999").status_code == 404


def test_search_is_case_insensitive(client):
    resp = client.get("/api/products/search?q=mug")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.get_json()["items"]]
    assert names == ["DevSecOps Mug"]


def test_search_partial_match(client):
    resp = client.get("/api/products/search?q=Hood")
    assert [p["name"] for p in resp.get_json()["items"]] == ["Pipeline Hoodie"]


def test_search_no_results(client):
    resp = client.get("/api/products/search?q=nonexistent-item")
    assert resp.get_json()["items"] == []


def test_products_q_parameter_uses_search(client):
    resp = client.get("/api/products?q=poster")
    assert [p["name"] for p in resp.get_json()["items"]] == ["Zero Trust Poster"]
