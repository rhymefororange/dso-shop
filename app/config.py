"""Конфігурація застосунку зі змінних середовища."""
import logging
import os
import secrets
import tempfile

log = logging.getLogger(__name__)


def _default_database_url():
    # Локальний запуск без PostgreSQL: SQLite-файл у тимчасовому каталозі.
    path = os.path.join(tempfile.gettempdir(), "dso-shop.sqlite3")
    return f"sqlite:///{path}"


class Config:
    """Значення читаються під час створення застосунку."""

    def __init__(self):
        self.DATABASE_URL = os.environ.get("DATABASE_URL") or _default_database_url()
        self.SEED_DATABASE = os.environ.get("SEED_DATABASE", "1").lower() in {"1", "true", "yes"}
        self.LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

        secret_key = os.environ.get("SECRET_KEY")
        if not secret_key:
            # Без SECRET_KEY токени будуть недійсними після перезапуску процесу.
            log.warning("SECRET_KEY is not set, generating an ephemeral key")
            secret_key = secrets.token_hex(32)
        self.SECRET_KEY = secret_key
        self.TOKEN_TTL_SECONDS = int(os.environ.get("TOKEN_TTL_SECONDS", "3600"))

        self.PAYMENT_GATEWAY_URL = os.environ.get("PAYMENT_GATEWAY_URL", "")
        self.PAYMENT_WEBHOOK_SECRET = os.environ.get("PAYMENT_WEBHOOK_SECRET", "")

        self.SMTP_HOST = os.environ.get("SMTP_HOST", "")
        self.SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
        self.MAIL_FROM = os.environ.get("MAIL_FROM", "no-reply@dso-shop.example")
        self.ADMIN_PASSWORD = os.environ.get("DSO_ADMIN_PASSWORD", "")
