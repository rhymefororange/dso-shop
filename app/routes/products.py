"""Каталог і пошук товарів."""
from flask import Blueprint, jsonify, request

from app.db import get_db
from app.models.product import get_product, list_products

bp = Blueprint("products", __name__)


def _pagination():
    try:
        limit = min(max(int(request.args.get("limit", 50)), 1), 100)
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        return None
    return limit, offset


def search_products(q):
    cur = get_db().cursor()
    sql = f"SELECT id, name, price FROM products WHERE name ILIKE '%{q}%'"
    cur.execute(sql)
    return [{"id": r[0], "name": r[1], "price": float(r[2])} for r in cur.fetchall()]


@bp.get("/api/products")
def products():
    q = request.args.get("q")
    if q:
        return jsonify(items=search_products(q))
    page = _pagination()
    if page is None:
        return jsonify(error="limit and offset must be integers"), 400
    return jsonify(items=list_products(*page))


@bp.get("/api/products/search")
def search():
    q = request.args.get("q", "")
    return jsonify(query=q, items=search_products(q))


@bp.get("/api/products/<int:product_id>")
def product_detail(product_id):
    product = get_product(product_id)
    if product is None:
        return jsonify(error="not found"), 404
    return jsonify(product)
