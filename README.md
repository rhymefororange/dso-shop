# DSO-Shop

Навчальний інтернет-магазин для лабораторних робіт з дисципліни «Інтеграція безпеки у життєвий цикл програмного забезпечення» (DevSecOps), НУ «Львівська політехніка».

Стек: Python 3.12, Flask 3, PostgreSQL, REST API (OpenAPI 3), статичний фронтенд, Docker, Kubernetes (kind), Terraform, Helm, GitHub Actions.

> **Увага.** Застосунок навмисно містить вразливості та помилки конфігурації, які ви знаходитимете й виправлятимете протягом курсу. Не розгортайте його в інтернеті, у спільних або робочих середовищах і не вводьте справжні персональні чи платіжні дані.

## Зміст

- [Архітектура](#архітектура)
- [Структура репозиторію](#структура-репозиторію)
- [Швидкий старт: Docker Compose](#швидкий-старт-docker-compose)
- [Запуск без Docker (venv + SQLite)](#запуск-без-docker-venv--sqlite)
- [Тести](#тести)
- [Конфігурація](#конфігурація)
- [Навчальні облікові записи](#навчальні-облікові-записи)
- [API](#api)
- [Платіжний шлюз DSOPay](#платіжний-шлюз-dsopay)
- [Розгортання в Kubernetes (kind)](#розгортання-в-kubernetes-kind)
- [Робота з форком](#робота-з-форком)

## Архітектура

```
                 ┌──────────────────────────── DSO-Shop ───────────────────────────┐
 Браузер ──HTTP──▶ gunicorn + Flask (app/)  ──SQL──▶ PostgreSQL                    │
                 │   routes/ models/ services/                                     │
                 └───────┬───────────────────────────▲─────────────────────────────┘
                         │ HTTPS (API-ключ)          │ HTTPS webhook (HMAC)
                         ▼                           │
                   Платіжний шлюз DSOPay ────────────┘          SMTP ◀── листи покупцям
```

- **Фронтенд** — статичні файли в `app/static/`, що звертаються до REST API.
- **API** — Flask-застосунок, створюється фабрикою `create_app()`; точка входу WSGI: **`app:create_app()`**.
- **База даних** — PostgreSQL (через psycopg 3); без `DATABASE_URL` застосунок автоматично використовує SQLite у тимчасовому каталозі (зручно для тестів і локального запуску).
- **Інтеграції** — навчальний платіжний шлюз DSOPay, поштовий сервіс (SMTP), у Kubernetes — секрети з Vault.

Детальний опис компонентів і потоків даних: [docs/architecture.md](docs/architecture.md).

## Структура репозиторію

```
dso-shop/
  app/                    # Flask-застосунок
    __init__.py           #   фабрика create_app()
    config.py             #   конфігурація зі змінних середовища
    db.py                 #   підключення до PostgreSQL / SQLite, схема БД
    routes/               #   HTTP-маршрути (health, products, auth, cart, orders, payments, admin)
    models/               #   доступ до даних і початкові дані (seed.py)
    services/             #   токени доступу, платежі, пошта
    static/               #   статичний фронтенд
  api/openapi.yaml        # специфікація REST API (OpenAPI 3.0)
  tests/                  # тести pytest
  requirements.txt        # залежності застосунку
  requirements-dev.txt    # залежності для розробки і тестів
  Dockerfile
  docker-compose.yml      # застосунок + PostgreSQL
  deploy/k8s/             # маніфести Kubernetes (Deployment dso-shop, Service)
  deploy/helm/dso-shop/   # Helm-чарт застосунку
  infra/terraform/        # Terraform: кластер kind, простір імен, PostgreSQL
  docs/architecture.md    # архітектура і потоки даних
  docs/security/          # артефакти безпеки (заповнюються в лабораторних)
  docs/adr/               # архітектурні рішення (ADR)
  .github/workflows/      # конвеєри GitHub Actions (ci.yml)
```

## Швидкий старт: Docker Compose

Потрібні Docker Engine 24+ і Docker Compose v2.24+.

```bash
cp .env.example .env          # необов'язково: задайте SECRET_KEY, DSO_ADMIN_PASSWORD тощо
docker compose up -d --build
curl -s http://localhost:8080/api/health
# {"database":"ok","status":"ok","version":"1.3.0"}
```

Вебінтерфейс: <http://localhost:8080/>. Зупинити: `docker compose down` (з видаленням даних БД: `docker compose down -v`).

Ім'я образу застосунку параметризоване змінною `DSO_IMAGE` (типово `dso-shop:local`), тож можна запустити вже опублікований образ без збирання:

```bash
DSO_IMAGE=ghcr.io/<логін>/dso-shop@sha256:<digest> docker compose up -d --no-build
```

Якщо порт 8080 зайнятий, змініть відображення порту в `docker-compose.yml` локально, не фіксуючи цю зміну.

## Запуск без Docker (venv + SQLite)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# режим розробки Flask (SQLite у тимчасовому каталозі)
flask --app "app:create_app()" run --port 8080

# або так само, як у контейнері
gunicorn --bind 127.0.0.1:8080 "app:create_app()"
```

Щоб працювати з PostgreSQL, задайте `DATABASE_URL`, наприклад `postgresql://dso:dso-local-dev@localhost:5432/dso_shop`.

## Тести

```bash
source .venv/bin/activate
pytest -q
```

Кожен тест отримує окрему SQLite-базу (`tests/conftest.py`), тож PostgreSQL для тестів не потрібен. Тест `tests/test_openapi.py` перевіряє, що `api/openapi.yaml` описує всі маршрути `/api/...` і лише їх: додаючи або змінюючи ендпоінт, оновлюйте специфікацію.

Конвеєр `.github/workflows/ci.yml` на кожен push у `main` і pull request запускає тести та збирає Docker-образ із перевіркою `/api/health`.

## Конфігурація

| Змінна | Призначення | Типово |
|---|---|---|
| `DATABASE_URL` | `postgresql://user:pass@host:5432/db` або `sqlite:////абсолютний/шлях.db` | SQLite у тимчасовому каталозі |
| `SECRET_KEY` | Ключ підпису токенів доступу (JWT) | генерується під час старту (токени втрачаються після перезапуску) |
| `TOKEN_TTL_SECONDS` | Строк дії токена | `3600` |
| `DSO_ADMIN_PASSWORD` | Пароль облікового запису `admin` під час першого заповнення БД | випадковий (вхід адміністратора вимкнено) |
| `SEED_DATABASE` | Заповнювати порожню БД початковими даними | `1` |
| `PAYMENT_GATEWAY_URL` | Адреса API платіжного шлюзу DSOPay | порожньо — режим пісочниці |
| `PAYMENT_API_KEY` | API-ключ DSOPay | — |
| `PAYMENT_WEBHOOK_SECRET` | Спільний секрет для перевірки підпису webhook | порожньо — webhook відхиляються |
| `SMTP_HOST`, `SMTP_PORT`, `MAIL_FROM` | Поштовий сервер | порожньо — листи не надсилаються |
| `LOG_LEVEL` | Рівень журналювання | `INFO` |

Локальні значення зберігайте у файлі `.env` (він у `.gitignore`); `docker compose` передає їх у контейнер застосунку.

## Навчальні облікові записи

Під час першого запуску порожня БД заповнюється каталогом із 12 товарів і обліковими записами:

| Логін | Пароль | Роль | Призначення |
|---|---|---|---|
| `test` | `test-password` | customer | Тестовий покупець для ручних перевірок і автентифікованого DAST |
| `admin` | значення `DSO_ADMIN_PASSWORD` | admin | Адміністрування каталогу |
| `alice` | випадковий | customer | Власниця замовлення №1 (для перевірок контролю доступу) |

Отримання токена:

```bash
TOKEN=$(curl -s -X POST http://localhost:8080/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"test","password":"test-password"}' | jq -r .access_token)
curl -s http://localhost:8080/api/cart -H "Authorization: Bearer $TOKEN"
```

## API

Повна специфікація — [api/openapi.yaml](api/openapi.yaml). Основні ендпоінти:

| Метод і шлях | Автентифікація | Опис |
|---|---|---|
| `GET /api/health` | — | Стан застосунку і БД |
| `GET /api/products` | — | Перелік товарів (`limit`, `offset`; з параметром `q` — пошук) |
| `GET /api/products/search?q=` | — | Пошук товарів за фрагментом назви |
| `GET /api/products/{id}` | — | Картка товару |
| `POST /api/auth/register` | — | Реєстрація покупця |
| `POST /api/auth/login` | — | Вхід, отримання `access_token` |
| `GET /api/auth/me` | Bearer | Поточний користувач |
| `POST /api/auth/password-reset` | — | Запит на відновлення пароля |
| `GET /api/cart`, `POST /api/cart/items`, `DELETE /api/cart/items/{id}` | Bearer | Кошик |
| `GET /api/orders`, `POST /api/orders` | Bearer | Мої замовлення, оформлення замовлення |
| `GET /api/orders/{id}` | Bearer | Деталі замовлення (власник або адміністратор) |
| `POST /api/payments/webhook` | Підпис HMAC | Сповіщення DSOPay про оплату |
| `GET/POST /api/admin/products`, `PUT/DELETE /api/admin/products/{id}`, `GET /api/admin/orders` | Bearer, роль admin | Адміністрування |

## Платіжний шлюз DSOPay

DSOPay — вигаданий платіжний шлюз, створений лише для курсу; справжнього сервісу з такою назвою застосунок не використовує. Без `PAYMENT_GATEWAY_URL` оплата працює в режимі пісочниці: замовлення отримує ідентифікатор платежу `sandbox-...` без мережевих запитів.

- **API-ключі** мають формат `dsopay_<середовище>_<32 символи [a-z0-9]>`, де середовище — `live` або `test`, наприклад `dsopay_test_` + 32 символи. Ключ передається в заголовку `Authorization: Bearer <ключ>` під час створення платежу (`POST {PAYMENT_GATEWAY_URL}/v1/payments`).
- **Webhook** `POST /api/payments/webhook` приймає JSON `{"order_id", "status", "payment_ref"}`; тіло підписується HMAC-SHA256 секретом `PAYMENT_WEBHOOK_SECRET`, підпис (hex) передається в заголовку `X-DSOPay-Signature`.

## Розгортання в Kubernetes (kind)

Потрібні kind, kubectl; для варіанта з Terraform — Terraform ≥ 1.6, для чарта — Helm.

**Варіант 1: kubectl.**

```bash
docker build -t dso-shop:dev .
kind create cluster --name dso-shop
kind load docker-image dso-shop:dev --name dso-shop
kubectl create namespace dso-shop
kubectl -n dso-shop apply -f deploy/k8s/
kubectl -n dso-shop set image deployment/dso-shop api=dso-shop:dev
kubectl -n dso-shop rollout status deployment/dso-shop
kubectl -n dso-shop port-forward svc/dso-shop 8080:80
```

Без Secret `dso-shop-db` застосунок працює з вбудованою SQLite-базою (демонстраційний режим).

**Варіант 2: Terraform + Helm.** Terraform створює кластер kind, простір імен `dso-shop`, Secret `dso-shop-db` (згенерований пароль) і PostgreSQL:

```bash
cd infra/terraform
terraform init
terraform apply
export KUBECONFIG=$(terraform output -raw kubeconfig_path)
cd ../..
kind load docker-image dso-shop:dev --name dso-shop
helm install dso-shop deploy/helm/dso-shop -n dso-shop --set image.tag=dev
```

Рендеринг чарта у YAML (наприклад, для сканування): `helm template dso-shop deploy/helm/dso-shop > rendered.yaml`.

## Робота з форком

1. Відкрийте сторінку репозиторію курсу і натисніть **Fork** (або **Use this template → Create a new repository**, якщо так вказав викладач). Форк має бути **публічним**: Code scanning, secret scanning і artifact attestations для публічних репозиторіїв безкоштовні.
2. У форку відкрийте вкладку **Actions** і дозвольте запуск workflow (у форках він вимкнений за замовчуванням).
3. Склонуйте форк і перевірте локальний запуск:
   ```bash
   git clone https://github.com/<ваш-логін>/dso-shop.git
   cd dso-shop
   docker compose up -d --build && curl -s http://localhost:8080/api/health
   ```
4. Кожну лабораторну роботу виконуйте в окремій гілці від актуального `main` і здавайте через pull request у `main` **власного форку** (не в репозиторій курсу):

   | ЛР | Гілка |
   |---|---|
   | 1 | `lab1-threat-model` |
   | 2 | `lab2-sast-secrets` |
   | 3 | `lab3-sca-sbom` |
   | 4 | `lab4-container-iac` |
   | 5 | `lab5-dast-signing` |

   У форку GitHub CLI за замовчуванням пропонує створити PR у батьківський репозиторій. Один раз виконайте `gh repo set-default <ваш-логін>/dso-shop`, а у вебінтерфейсі перевіряйте, що base repository — ваш форк.

5. Після злиття PR оновіть локальний `main` (`git checkout main && git pull`) перед початком наступної роботи.

Щоб отримати оновлення з репозиторію курсу: `git remote add upstream https://github.com/<репозиторій-курсу>/dso-shop.git && git fetch upstream && git merge upstream/main` (або кнопка **Sync fork** на GitHub).

## Ліцензія

[MIT](LICENSE)
