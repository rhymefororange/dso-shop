def test_login_success(client):
    resp = client.post("/api/auth/login", json={"username": "test", "password": "test-password"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["token_type"] == "Bearer"
    assert body["access_token"]


def test_login_wrong_password(client):
    resp = client.post("/api/auth/login", json={"username": "test", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_user_same_error(client):
    unknown = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
    wrong = client.post("/api/auth/login", json={"username": "test", "password": "x"})
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.get_json() == wrong.get_json()


def test_login_requires_json(client):
    assert client.post("/api/auth/login", data="x").status_code == 400


def test_me(client, user_headers):
    resp = client.get("/api/auth/me", headers=user_headers)
    assert resp.status_code == 200
    assert resp.get_json()["username"] == "test"
    assert "password_hash" not in resp.get_json()


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_register_and_login(client):
    resp = client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "bob@example.org", "password": "correct-horse-battery"},
    )
    assert resp.status_code == 201
    assert resp.get_json()["role"] == "customer"
    login = client.post(
        "/api/auth/login", json={"username": "bob", "password": "correct-horse-battery"}
    )
    assert login.status_code == 200


def test_register_validation(client):
    short = client.post(
        "/api/auth/register", json={"username": "eve", "email": "eve@example.org", "password": "x"}
    )
    assert short.status_code == 400
    dup = client.post(
        "/api/auth/register",
        json={"username": "test", "email": "other@example.org", "password": "long-enough-pass"},
    )
    assert dup.status_code == 409


def test_password_reset_does_not_reveal_accounts(client):
    known = client.post("/api/auth/password-reset", json={"email": "test@dso-shop.example"})
    unknown = client.post("/api/auth/password-reset", json={"email": "nobody@example.org"})
    assert known.status_code == unknown.status_code == 202
    assert known.get_json() == unknown.get_json()
