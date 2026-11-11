"""Перевірка стану застосунку."""
import logging

from flask import Blueprint, jsonify

from app.db import get_db

bp = Blueprint("health", __name__)
log = logging.getLogger(__name__)


@bp.get("/api/health")
def health():
    from app import __version__

    try:
        cur = get_db().cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        db_status = "ok"
    except Exception:  # noqa: BLE001 - стан БД повідомляється, а не піднімається
        log.exception("Database health check failed")
        db_status = "unavailable"
    status = 200 if db_status == "ok" else 503
    return jsonify(status="ok" if status == 200 else "degraded",
                   database=db_status, version=__version__), status
