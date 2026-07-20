def test_register_creates_subscriber(client):
    response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "supersecret", "name": "Ana"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["role"] == "subscriber"


def test_register_duplicate_email_conflicts(client):
    payload = {"email": "dup@example.com", "password": "supersecret", "name": "Ana"}
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201
    second = client.post("/auth/register", json=payload)
    assert second.status_code == 409


def test_login_returns_tokens(client):
    client.post(
        "/auth/register", json={"email": "login@example.com", "password": "supersecret", "name": "Ana"}
    )
    response = client.post("/auth/login", json={"email": "login@example.com", "password": "supersecret"})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_login_wrong_password_fails(client):
    client.post(
        "/auth/register", json={"email": "wrong@example.com", "password": "supersecret", "name": "Ana"}
    )
    response = client.post("/auth/login", json={"email": "wrong@example.com", "password": "incorrect"})
    assert response.status_code == 401


def test_login_unknown_email_fails(client):
    response = client.post("/auth/login", json={"email": "ghost@example.com", "password": "supersecret"})
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/auth/me")
    assert response.status_code == 403


def test_me_rejects_garbage_token(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_me_returns_current_user(client):
    client.post("/auth/register", json={"email": "me@example.com", "password": "supersecret", "name": "Ana"})
    login = client.post("/auth/login", json={"email": "me@example.com", "password": "supersecret"})
    token = login.json()["access_token"]

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


def test_refresh_issues_new_access_token(client):
    client.post(
        "/auth/register", json={"email": "refresh@example.com", "password": "supersecret", "name": "Ana"}
    )
    login = client.post("/auth/login", json={"email": "refresh@example.com", "password": "supersecret"})
    refresh_token = login.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_rejects_access_token(client):
    client.post(
        "/auth/register", json={"email": "swap@example.com", "password": "supersecret", "name": "Ana"}
    )
    login = client.post("/auth/login", json={"email": "swap@example.com", "password": "supersecret"})
    access_token = login.json()["access_token"]

    response = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401


def test_admin_route_rejects_subscriber(client):
    client.post("/auth/register", json={"email": "sub@example.com", "password": "supersecret", "name": "Ana"})
    login = client.post("/auth/login", json={"email": "sub@example.com", "password": "supersecret"})
    token = login.json()["access_token"]

    response = client.get("/admin/markets", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
