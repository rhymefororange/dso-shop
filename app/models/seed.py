"""Початкові дані для локального запуску і навчальних сценаріїв."""
import logging
import secrets

from app.models.user import create_user

log = logging.getLogger(__name__)

PRODUCTS = [
    ("DevSecOps Mug", "Керамічна чашка 350 мл з логотипом DSO-Shop", "12.50", 120),
    ("Shift-Left T-Shirt", "Футболка з бавовни, принт «Shift left, ship safe»", "19.90", 80),
    ("Threat Modeling Cards", "Колода карток STRIDE для командних сесій", "24.00", 40),
    ("Secure Coding Handbook", "Довідник із безпечного кодування, 320 с.", "35.00", 25),
    ("Hardware Security Key", "Ключ FIDO2 / WebAuthn з USB-C", "49.00", 30),
    ("Privacy Webcam Cover", "Набір із трьох шторок для камери ноутбука", "4.90", 300),
    ("Pipeline Hoodie", "Худі з принтом схеми CI/CD конвеєра", "39.00", 50),
    ("Container Sticker Pack", "Набір наліпок: Docker, Kubernetes, Sigstore", "6.50", 500),
    ("SBOM Notebook", "Блокнот A5 у крапку, 120 аркушів", "8.00", 150),
    ("Incident Response Playbook", "Друкований посібник із реагування на інциденти", "29.00", 20),
    ("Zero Trust Poster", "Плакат A2 з принципами Zero Trust", "11.00", 60),
    ("Canary Token Keychain", "Брелок у формі канарки", "5.50", 200),
]

# Навчальний обліковий запис покупця (описаний у README, використовується в ЛР5).
TEST_USER = {"username": "test", "email": "test@dso-shop.example", "password": "test-password"}


def seed_if_empty(conn, admin_password=""):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] > 0:
        return

    for name, description, price, stock in PRODUCTS:
        cur.execute(
            "INSERT INTO products (name, description, price, stock, image_url) "
            "VALUES (%s, %s, %s, %s, %s)",
            (name, description, price, stock, ""),
        )
    conn.commit()

    create_user(conn, TEST_USER["username"], TEST_USER["email"], TEST_USER["password"])

    if not admin_password:
        # Без DSO_ADMIN_PASSWORD вхід адміністратора неможливий (пароль випадковий).
        admin_password = secrets.token_urlsafe(24)
        log.info("DSO_ADMIN_PASSWORD is not set; admin login is disabled")
    create_user(conn, "admin", "admin@dso-shop.example", admin_password, role="admin")

    # Другий покупець із замовленням — для перевірки контролю доступу до чужих замовлень.
    alice_id = create_user(conn, "alice", "alice@dso-shop.example", secrets.token_urlsafe(24))
    cur.execute(
        "INSERT INTO orders (user_id, status, total, payment_ref) VALUES (%s, %s, %s, %s)",
        (alice_id, "paid", "36.00", "demo-0001"),
    )
    cur.execute("SELECT id FROM orders WHERE payment_ref = %s", ("demo-0001",))
    order_id = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
        "VALUES (%s, %s, %s, %s)",
        (order_id, 1, 2, "12.50"),
    )
    cur.execute(
        "INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
        "VALUES (%s, %s, %s, %s)",
        (order_id, 12, 2, "5.50"),
    )
    conn.commit()
    log.info("Database seeded with %d products", len(PRODUCTS))
