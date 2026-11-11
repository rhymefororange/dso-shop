import hashlib
import hmac
import json

SECRET = b"pytest-webhook-secret"


def _create_order(client, headers):
    client.post("/api/cart/items", json={"product_id": 4, "quantity": 1}, headers=headers)
    return client.post("/api/orders", headers=headers).get_json()["order"]


def _signed(payload):
    body = json.dumps(payload).encode()
    signature = hmac.new(SECRET, body, hashlib.sha256).hexdigest()
    return body, {"X-DSOPay-Signature": signature, "Content-Type": "application/json"}


def test_webhook_rejects_missing_signature(client):
    resp = client.post("/api/payments/webhook", json={"order_id": 1, "status": "paid"})
    assert resp.status_code == 401


def test_webhook_rejects_bad_signature(client):
    resp = client.post(
        "/api/payments/webhook",
        json={"order_id": 1, "status": "paid"},
        headers={"X-DSOPay-Signature": "00" * 32},
    )
    assert resp.status_code == 401


def test_webhook_marks_order_paid(client, user_headers):
    order = _create_order(client, user_headers)
    body, headers = _signed(
        {"order_id": order["id"], "status": "paid", "payment_ref": order["payment_ref"]}
    )
    resp = client.post("/api/payments/webhook", data=body, headers=headers)
    assert resp.status_code == 200
    detail = client.get(f"/api/orders/{order['id']}", headers=user_headers).get_json()
    assert detail["status"] == "paid"

    # Повторна доставка того самого webhook не змінює стан.
    again = client.post("/api/payments/webhook", data=body, headers=headers)
    assert again.get_json()["duplicate"] is True


def test_webhook_payment_ref_must_match(client, user_headers):
    order = _create_order(client, user_headers)
    body, headers = _signed({"order_id": order["id"], "status": "paid", "payment_ref": "other"})
    assert client.post("/api/payments/webhook", data=body, headers=headers).status_code == 409
