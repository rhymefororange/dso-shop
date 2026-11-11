"""Статичний фронтенд і обробники помилок."""
from flask import Blueprint, current_app, jsonify, send_from_directory

bp = Blueprint("web", __name__)


@bp.get("/")
def index():
    return send_from_directory(current_app.static_folder, "index.html")


@bp.app_errorhandler(404)
def not_found(_err):
    return jsonify(error="not found"), 404


@bp.app_errorhandler(405)
def method_not_allowed(_err):
    return jsonify(error="method not allowed"), 405


@bp.app_errorhandler(500)
def internal_error(_err):
    return jsonify(error="internal server error"), 500
