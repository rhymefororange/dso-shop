"""DSO-Shop — навчальний інтернет-магазин (Flask + PostgreSQL).

Точка входу для WSGI-сервера: ``app:create_app()``.
"""
import logging

from flask import Flask

from app.config import Config
from app import db

__version__ = "1.3.0"


def create_app(config_overrides=None):
    """Фабрика застосунку Flask."""
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config.from_object(Config())
    if config_overrides:
        app.config.update(config_overrides)

    logging.basicConfig(
        level=app.config["LOG_LEVEL"],
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    db.init_app(app)

    from app.routes import admin, auth, cart, health, orders, payments, products, web

    app.register_blueprint(web.bp)
    app.register_blueprint(health.bp)
    app.register_blueprint(products.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(cart.bp)
    app.register_blueprint(orders.bp)
    app.register_blueprint(payments.bp)
    app.register_blueprint(admin.bp)

    return app

