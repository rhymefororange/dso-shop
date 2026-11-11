"""Webhook платіжного шлюзу DSOPay."""
from flask import Blueprint, jsonify, request

from app.models.order import get_order, set_payment
from app.services.payments import verify_webhook_signature

bp = Blueprint("payments", __name__, url_prefix="/api/payments")

ALLOWED_STATUSES = {"paid", "failed"}


@bp.post("/webhook")
def webhook():
    body = request.get_data()
    if not verify_webhook_signature(body, request.headers.get("X-DSOPay-Signature", "")):
        return jsonify(error="invalid signature"), 401
    data = request.get_json(silent=True) or {}
    try:
        order_id = int(data.get("order_id"))
    except (TypeError, ValueError):
        return jsonify(error="order_id must be an integer"), 400
    status = data.get("status")
    order = get_order(order_id)
    if order is None:
        return jsonify(error="order not found"), 404
    if status not in ALLOWED_STATUSES:
        return jsonify(error="unsupported status"), 400
    if order["payment_ref"] != data.get("payment_ref"):
        return jsonify(error="payment reference mismatch"), 409
    if order["status"] != "pending":
        return jsonify(status=order["status"], duplicate=True), 200
    set_payment(order_id, status=status)
    return jsonify(status=status), 200
