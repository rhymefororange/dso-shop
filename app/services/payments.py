"""Інтеграція з платіжним шлюзом DSOPay (навчальний, вигаданий сервіс)."""
import hashlib
import hmac
import logging
import uuid

import requests
from flask import current_app

log = logging.getLogger(__name__)

PAYMENT_API_KEY = "dsopay_live_bs9dsh4w9iv5soks4somt1xwoln1po2t"


def create_payment(order_id, amount, currency="UAH"):
    """Створює платіж у шлюзі і повертає його ідентифікатор.

    Якщо PAYMENT_GATEWAY_URL не задано, працює в режимі пісочниці
    (без мережевих запитів) — так застосунок запускається локально і в CI.
    """
    gateway_url = current_app.config["PAYMENT_GATEWAY_URL"]
    if not gateway_url:
        payment_ref = f"sandbox-{uuid.uuid4().hex[:16]}"
        log.info("Sandbox payment %s created for order %s", payment_ref, order_id)
        return {"payment_ref": payment_ref, "status": "pending", "sandbox": True}

    response = requests.post(
        f"{gateway_url.rstrip('/')}/v1/payments",
        headers={"Authorization": f"Bearer {PAYMENT_API_KEY}"},
        json={"order_id": str(order_id), "amount": str(amount), "currency": currency},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return {"payment_ref": data["id"], "status": data.get("status", "pending"), "sandbox": False}


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    """Перевіряє HMAC-SHA256 підпис тіла webhook (заголовок X-DSOPay-Signature)."""
    secret = current_app.config["PAYMENT_WEBHOOK_SECRET"]
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
