"""Адміністрування каталогу і перегляд замовлень (роль admin)."""
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

from app.models.order import list_orders
from app.models.product import (
    create_product,
    delete_product,
    get_product,
    list_products,
    update_product,
)
from app.services.auth import admin_required

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _validate_product(data, partial=False):
    clean = {}
    if "name" in data or not partial:
        name = str(data.get("name", "")).strip()
        if not 1 <= len(name) <= 200:
            return None, "name is required (1-200 characters)"
        clean["name"] = name
    if "description" in data:
        clean["description"] = str(data["description"])[:2000]
    if "price" in data or not partial:
        try:
            price = Decimal(str(data.get("price")))
        except InvalidOperation:
            return None, "price must be a number"
        if price <= 0:
            return None, "price must be positive"
        clean["price"] = str(price.quantize(Decimal("0.01")))
    if "stock" in data:
        try:
            clean["stock"] = max(int(data["stock"]), 0)
        except (TypeError, ValueError):
            return None, "stock must be an integer"
    return clean, None


@bp.get("/products")
@admin_required
def admin_list_products():
    return jsonify(items=list_products(limit=100))


@bp.post("/products")
@admin_required
def admin_create_product():
    data, error = _validate_product(request.get_json(silent=True) or {})
    if error:
        return jsonify(error=error), 400
    product = create_product(
        data["name"], data.get("description", ""), data["price"], data.get("stock", 0)
    )
    return jsonify(product), 201


@bp.put("/products/<int:product_id>")
@admin_required
def admin_update_product(product_id):
    if get_product(product_id) is None:
        return jsonify(error="not found"), 404
    data, error = _validate_product(request.get_json(silent=True) or {}, partial=True)
    if error:
        return jsonify(error=error), 400
    return jsonify(update_product(product_id, data))


@bp.delete("/products/<int:product_id>")
@admin_required
def admin_delete_product(product_id):
    result = delete_product(product_id)
    if result is None:
        return jsonify(error="product is referenced by orders"), 409
    if not result:
        return jsonify(error="not found"), 404
    return "", 204


@bp.get("/orders")
@admin_required
def admin_orders():
    return jsonify(items=list_orders())
