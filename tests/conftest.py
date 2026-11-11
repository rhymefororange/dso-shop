"""Спільні фікстури pytest: ізольована SQLite-база для кожного тесту."""
import os

import pytest

# Тестове оточення не використовує зовнішніх сервісів і справжніх облікових даних.
os.environ.setdefault("SECRET_KEY", "pytest-only-secret-key-not-for-production-use")
os.environ.setdefault("PAYMENT_API_KEY", "pytest-placeholder")
os.environ.pop("PAYMENT_GATEWAY_URL", None)
os.environ.pop("SMTP_HOST", None)

from app import create_app  # noqa: E402

ADMIN_PASSWORD = "pytest-admin-password"


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "DATABASE_URL": f"sqlite:///{tmp_path / 'test.sqlite3'}",
            "ADMIN_PASSWORD": ADMIN_PASSWORD,
            "PAYMENT_WEBHOOK_SECRET": "pytest-webhook-secret",
        }
    )
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, username, password):
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.get_json()
    return {"Authorization": f"Bearer {resp.get_json()['access_token']}"}


@pytest.fixture()
def user_headers(client):
    return login(client, "test", "test-password")


@pytest.fixture()
def admin_headers(client):
    return login(client, "admin", ADMIN_PASSWORD)
