def test_admin_endpoints_require_auth(client):
    assert client.get("/api/admin/products").status_code == 401


def test_admin_endpoints_forbidden_for_customer(client, user_headers):
    assert client.get("/api/admin/products", headers=user_headers).status_code == 403
    resp = client.post(
        "/api/admin/products", json={"name": "X", "price": "1.00"}, headers=user_headers
    )
    assert resp.status_code == 403


def test_admin_product_crud(client, admin_headers):
    resp = client.post(
        "/api/admin/products",
        json={"name": "OWASP Socks", "description": "Шкарпетки", "price": "7.25", "stock": 10},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    product = resp.get_json()
    assert product["price"] == 7.25

    resp = client.put(
        f"/api/admin/products/{product['id']}", json={"price": "8.00"}, headers=admin_headers
    )
    assert resp.get_json()["price"] == 8.0

    assert client.delete(f"/api/admin/products/{product['id']}", headers=admin_headers).status_code == 204
    assert client.get(f"/api/products/{product['id']}").status_code == 404


def test_admin_product_validation(client, admin_headers):
    resp = client.post("/api/admin/products", json={"name": "", "price": "1"}, headers=admin_headers)
    assert resp.status_code == 400
    resp = client.post("/api/admin/products", json={"name": "A", "price": "-1"}, headers=admin_headers)
    assert resp.status_code == 400


def test_admin_cannot_delete_ordered_product(client, admin_headers):
    assert client.delete("/api/admin/products/1", headers=admin_headers).status_code == 409


def test_admin_orders(client, admin_headers):
    resp = client.get("/api/admin/orders", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()["items"][0]["id"] == 1
