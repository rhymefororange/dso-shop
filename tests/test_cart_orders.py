def test_cart_requires_auth(client):
    assert client.get("/api/cart").status_code == 401


def test_cart_add_and_remove(client, user_headers):
    resp = client.post("/api/cart/items", json={"product_id": 1, "quantity": 2}, headers=user_headers)
    assert resp.status_code == 200
    cart = resp.get_json()
    assert cart["items"][0]["quantity"] == 2
    assert cart["total"] == 25.0
    resp = client.delete("/api/cart/items/1", headers=user_headers)
    assert resp.get_json()["items"] == []


def test_cart_validation(client, user_headers):
    bad_qty = client.post(
        "/api/cart/items", json={"product_id": 1, "quantity": 0}, headers=user_headers
    )
    assert bad_qty.status_code == 400
    missing = client.post(
        "/api/cart/items", json={"product_id": 999, "quantity": 1}, headers=user_headers
    )
    assert missing.status_code == 404


def test_checkout_uses_catalog_prices(client, user_headers):
    client.post("/api/cart/items", json={"product_id": 2, "quantity": 1}, headers=user_headers)
    client.post("/api/cart/items", json={"product_id": 6, "quantity": 3}, headers=user_headers)
    resp = client.post("/api/orders", json={"total": 0.01}, headers=user_headers)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["order"]["total"] == 34.6
    assert body["order"]["status"] == "pending"
    assert body["payment"]["sandbox"] is True
    assert client.get("/api/cart", headers=user_headers).get_json()["items"] == []


def test_checkout_empty_cart(client, user_headers):
    assert client.post("/api/orders", headers=user_headers).status_code == 400


def test_order_visible_to_owner(client, user_headers):
    client.post("/api/cart/items", json={"product_id": 3, "quantity": 1}, headers=user_headers)
    order_id = client.post("/api/orders", headers=user_headers).get_json()["order"]["id"]
    resp = client.get(f"/api/orders/{order_id}", headers=user_headers)
    assert resp.status_code == 200
    assert resp.get_json()["items"][0]["product_id"] == 3
    assert len(client.get("/api/orders", headers=user_headers).get_json()["items"]) == 1


def test_foreign_order_is_not_visible(client, user_headers):
    # Замовлення №1 належить іншому покупцю (seed).
    assert client.get("/api/orders/1", headers=user_headers).status_code == 404


def test_admin_can_see_any_order(client, admin_headers):
    assert client.get("/api/orders/1", headers=admin_headers).status_code == 200
