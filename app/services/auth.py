"""Видача і перевірка токенів доступу (JWT, HS256)."""
import functools
import time

import jwt
from flask import current_app, g, jsonify, request

from app.models.user import get_user_by_id

ALGORITHM = "HS256"


def issue_token(user):
    now = int(time.time())
    payload = {
        "sub": str(user["id"]),
        "role": user["role"],
        "iat": now,
        "exp": now + current_app.config["TOKEN_TTL_SECONDS"],
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm=ALGORITHM)


def _current_user():
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        return None
    return get_user_by_id(int(payload["sub"]))


def login_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        user = _current_user()
        if user is None:
            return jsonify(error="authentication required"), 401
        g.user = user
        return view(*args, **kwargs)

    return wrapper


def admin_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        user = _current_user()
        if user is None:
            return jsonify(error="authentication required"), 401
        if user["role"] != "admin":
            return jsonify(error="forbidden"), 403
        g.user = user
        return view(*args, **kwargs)

    return wrapper
