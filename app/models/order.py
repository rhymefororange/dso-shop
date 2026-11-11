"""Кошик і замовлення."""
from decimal import Decimal

from app.db import get_db


def get_cart(user_id):
    cur = get_db().cursor()
    cur.execute(
        "SELECT p.id, p.name, p.price, c.quantity FROM cart_items c "
        "JOIN products p ON p.id = c.product_id WHERE c.user_id = %s ORDER BY p.id",
        (user_id,),
    )
    items = [
        {"product_id": r[0], "name": r[1], "unit_price": float(r[2]), "quantity": r[3]}
        for r in cur.fetchall()
    ]
    total = sum(Decimal(str(i["unit_price"])) * i["quantity"] for i in items)
    return {"items": items, "total": float(total)}


def set_cart_item(user_id, product_id, quantity):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM cart_items WHERE user_id = %s AND product_id = %s", (user_id, product_id)
    )
    if quantity > 0:
        cur.execute(
            "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (%s, %s, %s)",
            (user_id, product_id, quantity),
        )
    conn.commit()


def clear_cart(conn, user_id):
    conn.cursor().execute("DELETE FROM cart_items WHERE user_id = %s", (user_id,))


def create_order_from_cart(user_id):
    """Створює замовлення; ціни беруться з каталогу, а не з запиту клієнта."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT p.id, p.price, c.quantity, p.stock FROM cart_items c "
        "JOIN products p ON p.id = c.product_id WHERE c.user_id = %s",
        (user_id,),
    )
    rows = cur.fetchall()
    if not rows:
        return None, "cart is empty"
    for _pid, _price, qty, stock in rows:
        if qty > stock:
            return None, "insufficient stock"
    total = sum(Decimal(str(price)) * qty for _pid, price, qty, _stock in rows)
    cur.execute(
        "INSERT INTO orders (user_id, status, total) VALUES (%s, 'pending', %s) RETURNING id",
        (user_id, str(total)),
    )
    order_id = cur.fetchone()[0]
    for pid, price, qty, _stock in rows:
        cur.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
            "VALUES (%s, %s, %s, %s)",
            (order_id, pid, qty, str(price)),
        )
        cur.execute("UPDATE products SET stock = stock - %s WHERE id = %s", (qty, pid))
    clear_cart(conn, user_id)
    conn.commit()
    return order_id, None


def get_order(order_id):
    cur = get_db().cursor()
    cur.execute(
        "SELECT id, user_id, status, total, payment_ref, created_at FROM orders WHERE id = %s",
        (order_id,),
    )
    row = cur.fetchone()
    if row is None:
        return None
    cur.execute(
        "SELECT oi.product_id, p.name, oi.quantity, oi.unit_price FROM order_items oi "
        "JOIN products p ON p.id = oi.product_id WHERE oi.order_id = %s ORDER BY oi.product_id",
        (order_id,),
    )
    items = [
        {"product_id": r[0], "name": r[1], "quantity": r[2], "unit_price": float(r[3])}
        for r in cur.fetchall()
    ]
    return {
        "id": row[0],
        "user_id": row[1],
        "status": row[2],
        "total": float(row[3]),
        "payment_ref": row[4],
        "created_at": str(row[5]),
        "items": items,
    }


def list_orders(user_id=None):
    cur = get_db().cursor()
    if user_id is None:
        cur.execute("SELECT id FROM orders ORDER BY id")
    else:
        cur.execute("SELECT id FROM orders WHERE user_id = %s ORDER BY id", (user_id,))
    return [get_order(r[0]) for r in cur.fetchall()]


def set_payment(order_id, payment_ref=None, status=None):
    conn = get_db()
    cur = conn.cursor()
    if payment_ref is not None:
        cur.execute("UPDATE orders SET payment_ref = %s WHERE id = %s", (payment_ref, order_id))
    if status is not None:
        cur.execute("UPDATE orders SET status = %s WHERE id = %s", (status, order_id))
    conn.commit()
