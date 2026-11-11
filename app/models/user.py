"""Облікові записи користувачів."""
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db

def _to_dict(row):
    if row is None:
        return None
    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "password_hash": row[3],
        "role": row[4],
    }


def public_view(user):
    return {k: user[k] for k in ("id", "username", "email", "role")}


def get_user_by_id(user_id):
    cur = get_db().cursor()
    cur.execute("SELECT id, username, email, password_hash, role FROM users WHERE id = %s", (user_id,))
    return _to_dict(cur.fetchone())


def get_user_by_username(username):
    cur = get_db().cursor()
    cur.execute("SELECT id, username, email, password_hash, role FROM users WHERE username = %s", (username,))
    return _to_dict(cur.fetchone())


def get_user_by_email(email):
    cur = get_db().cursor()
    cur.execute("SELECT id, username, email, password_hash, role FROM users WHERE email = %s", (email,))
    return _to_dict(cur.fetchone())


def create_user(conn, username, email, password, role="customer"):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, email, password_hash, role) "
        "VALUES (%s, %s, %s, %s) RETURNING id",
        (username, email, generate_password_hash(password), role),
    )
    user_id = cur.fetchone()[0]
    conn.commit()
    return user_id


def verify_password(user, password):
    return check_password_hash(user["password_hash"], password)
