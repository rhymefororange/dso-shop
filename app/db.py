"""Доступ до бази даних: PostgreSQL (psycopg 3) або SQLite для локальних тестів.

Обидва драйвери використовуються через спільний інтерфейс DB-API:
``conn = get_db(); cur = conn.cursor(); cur.execute(sql, params)``.
Плейсхолдер параметрів — ``%s`` (стиль psycopg); для SQLite його
перетворює обгортка ``_SQLiteCursor``.
"""
import logging
import re
import sqlite3
from urllib.parse import urlparse

from flask import current_app, g

log = logging.getLogger(__name__)

_ILIKE = re.compile(r"\bILIKE\b", re.IGNORECASE)


class _SQLiteCursor:
    """Мінімальна сумісність SQLite із синтаксисом PostgreSQL, який використовує DSO-Shop."""

    def __init__(self, cursor):
        self._cur = cursor

    def execute(self, sql, params=None):
        # SQLite не має ILIKE; LIKE у SQLite і так нечутливий до регістру для ASCII.
        sql = _ILIKE.sub("LIKE", sql)
        if params is None:
            return self._cur.execute(sql)
        return self._cur.execute(sql.replace("%s", "?"), params)

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    @property
    def rowcount(self):
        return self._cur.rowcount

    def close(self):
        self._cur.close()


class _SQLiteConnection:
    def __init__(self, path):
        self._conn = sqlite3.connect(path)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self.dialect = "sqlite"

    def cursor(self):
        return _SQLiteCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


class _PostgresConnection:
    def __init__(self, url):
        import psycopg  # імпорт лише за потреби: SQLite-режим працює і без драйвера

        self._conn = psycopg.connect(url)
        self.dialect = "postgresql"

    def cursor(self):
        return self._conn.cursor()

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()


def connect(url):
    parsed = urlparse(url)
    if parsed.scheme == "sqlite":
        # sqlite:///relative.db або sqlite:////abs/path.db
        return _SQLiteConnection(url[len("sqlite:///"):] or ":memory:")
    if parsed.scheme in {"postgres", "postgresql"}:
        return _PostgresConnection(url)
    raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")


def get_db():
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE_URL"])
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id {pk},
    username VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(16) NOT NULL DEFAULT 'customer',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS products (
    id {pk},
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    price NUMERIC(10, 2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    image_url VARCHAR(255) NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS cart_items (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (user_id, product_id)
);
CREATE TABLE IF NOT EXISTS orders (
    id {pk},
    user_id INTEGER NOT NULL REFERENCES users(id),
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    total NUMERIC(10, 2) NOT NULL,
    payment_ref VARCHAR(64),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS order_items (
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (order_id, product_id)
);
"""

PK_TYPES = {
    "postgresql": "SERIAL PRIMARY KEY",
    "sqlite": "INTEGER PRIMARY KEY AUTOINCREMENT",
}


def init_schema(conn):
    cur = conn.cursor()
    for statement in SCHEMA.format(pk=PK_TYPES[conn.dialect]).split(";"):
        if statement.strip():
            cur.execute(statement)
    conn.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        conn = get_db()
        init_schema(conn)
        if app.config["SEED_DATABASE"]:
            from app.models.seed import seed_if_empty

            seed_if_empty(conn, admin_password=app.config["ADMIN_PASSWORD"])
    log.info("Database ready (%s)", urlparse(app.config["DATABASE_URL"]).scheme)
