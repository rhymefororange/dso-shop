"""Реєстрація, вхід, відновлення пароля."""
import re

from flask import Blueprint, g, jsonify, request

from app.db import get_db
from app.models.user import (
    create_user,
    get_user_by_email,
    get_user_by_username,
    public_view,
    verify_password,
)
from app.services.auth import issue_token, login_required
from app.services.mailer import send_mail

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]{3,64}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


@bp.post("/register")
def register():
    data = _json_body()
    if data is None:
        return jsonify(error="JSON body required"), 400
    username = str(data.get("username", ""))
    email = str(data.get("email", ""))
    password = str(data.get("password", ""))
    if not USERNAME_RE.match(username) or not EMAIL_RE.match(email):
        return jsonify(error="invalid username or email"), 400
    if len(password) < 12:
        return jsonify(error="password must be at least 12 characters"), 400
    if get_user_by_username(username) or get_user_by_email(email):
        return jsonify(error="user already exists"), 409
    user_id = create_user(get_db(), username, email, password)
    return jsonify(id=user_id, username=username, email=email, role="customer"), 201


@bp.post("/login")
def login():
    data = _json_body()
    if data is None:
        return jsonify(error="JSON body required"), 400
    user = get_user_by_username(str(data.get("username", "")))
    if user is None or not verify_password(user, str(data.get("password", ""))):
        return jsonify(error="invalid credentials"), 401
    return jsonify(access_token=issue_token(user), token_type="Bearer")


@bp.get("/me")
@login_required
def me():
    return jsonify(public_view(g.user))


@bp.post("/password-reset")
def password_reset():
    data = _json_body()
    if data is None:
        return jsonify(error="JSON body required"), 400
    user = get_user_by_email(str(data.get("email", "")))
    if user is not None:
        send_mail(
            user["email"],
            "DSO-Shop: відновлення пароля",
            "Ви запросили відновлення пароля. Якщо це були не ви, проігноруйте цей лист.",
        )
    # Однакова відповідь незалежно від існування облікового запису.
    return jsonify(status="if the account exists, an email has been sent"), 202
