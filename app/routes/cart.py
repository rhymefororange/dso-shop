"""Кошик покупця."""
from flask import Blueprint, g, jsonify, request

from app.models.order import get_cart, set_cart_item
from app.models.product import get_product
from app.services.auth import login_required

bp = Blueprint("cart", __name__, url_prefix="/api/cart")


@bp.get("")
@login_required
def view_cart():
    return jsonify(get_cart(g.user["id"]))


@bp.post("/items")
@login_required
def add_item():
    data = request.get_json(silent=True) or {}
    try:
        product_id = int(data.get("product_id"))
        quantity = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        return jsonify(error="product_id and quantity must be integers"), 400
    if not 1 <= quantity <= 99:
        return jsonify(error="quantity must be between 1 and 99"), 400
    if get_product(product_id) is None:
        return jsonify(error="product not found"), 404
    set_cart_item(g.user["id"], product_id, quantity)
    return jsonify(get_cart(g.user["id"])), 200


@bp.delete("/items/<int:product_id>")
@login_required
def remove_item(product_id):
    set_cart_item(g.user["id"], product_id, 0)
    return jsonify(get_cart(g.user["id"]))
