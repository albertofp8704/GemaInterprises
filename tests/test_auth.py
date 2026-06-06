def test_register_new_user(client):
    r = client.post("/api/auth/register", json={"email": "newuser@test.com", "password": "pass1234"})
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert data["user"]["email"] == "newuser@test.com"
    assert data["user"]["plan"] == "free"


def test_register_duplicate_email(client):
    client.post("/api/auth/register", json={"email": "dup@test.com", "password": "pass"})
    r = client.post("/api/auth/register", json={"email": "dup@test.com", "password": "pass"})
    assert r.status_code == 400


def test_login_valid(client):
    client.post("/api/auth/register", json={"email": "login@test.com", "password": "mypassword"})
    r = client.post("/api/auth/login", json={"email": "login@test.com", "password": "mypassword"})
    assert r.status_code == 200
    assert "token" in r.json()


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={"email": "goat@test.com", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_email(client):
    r = client.post("/api/auth/login", json={"email": "nobody@test.com", "password": "pass"})
    assert r.status_code == 401


def test_me_returns_user(client, headers):
    r = client.get("/api/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "goat@test.com"


def test_me_unauthorized(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 403


def test_me_invalid_token(client):
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert r.status_code == 401
