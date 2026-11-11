"""Оформлення і перегляд замовлень."""
from flask import Blueprint, g, jsonify

from app.models.order import create_order_from_cart, get_order, list_orders, set_payment
from app.services.auth import login_required
from app.services.payments import create_payment

bp = Blueprint("orders", __name__, url_prefix="/api/orders")


@bp.post("")
@login_required
def checkout():
    order_id, error = create_order_from_cart(g.user["id"])
    if error:
        return jsonify(error=error), 400
    order = get_order(order_id)
    payment = create_payment(order_id, order["total"])
    set_payment(order_id, payment_ref=payment["payment_ref"])
    order = get_order(order_id)
    return jsonify(order=order, payment=payment), 201


@bp.get("")
@login_required
def my_orders():
    return jsonify(items=list_orders(g.user["id"]))


@bp.get("/<int:order_id>")
@login_required
def order_detail(order_id):
    order = get_order(order_id)
    if order is None or (order["user_id"] != g.user["id"] and g.user["role"] != "admin"):
        return jsonify(error="not found"), 404
    return jsonify(order)
