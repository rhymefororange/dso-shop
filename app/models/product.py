"""Каталог товарів."""
from app.db import get_db

def product_row_to_dict(row):
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "price": float(row[3]),
        "stock": row[4],
        "image_url": row[5],
    }


def list_products(limit=50, offset=0):
    cur = get_db().cursor()
    cur.execute(
        "SELECT id, name, description, price, stock, image_url FROM products "
        "ORDER BY id LIMIT %s OFFSET %s",
        (limit, offset),
    )
    return [product_row_to_dict(r) for r in cur.fetchall()]


def get_product(product_id):
    cur = get_db().cursor()
    cur.execute(
        "SELECT id, name, description, price, stock, image_url FROM products WHERE id = %s",
        (product_id,),
    )
    row = cur.fetchone()
    return product_row_to_dict(row) if row else None


def create_product(name, description, price, stock, image_url=""):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (name, description, price, stock, image_url) "
        "VALUES (%s, %s, %s, %s, %s) RETURNING id",
        (name, description, price, stock, image_url),
    )
    product_id = cur.fetchone()[0]
    conn.commit()
    return get_product(product_id)


def update_product(product_id, fields):
    allowed = ("name", "description", "price", "stock", "image_url")
    updates = [(k, fields[k]) for k in allowed if k in fields]
    if not updates:
        return get_product(product_id)
    assignments = ", ".join(f"{k} = %s" for k, _ in updates)
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE products SET {assignments} WHERE id = %s",
        tuple(v for _, v in updates) + (product_id,),
    )
    conn.commit()
    return get_product(product_id)


def delete_product(product_id):
    """Повертає True/False (видалено/не знайдено) або None, якщо товар є в замовленнях."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
        deleted = cur.rowcount > 0
        conn.commit()
    except Exception:  # noqa: BLE001 - порушення зовнішнього ключа (sqlite3/psycopg)
        conn.rollback()
        return None
    return deleted
