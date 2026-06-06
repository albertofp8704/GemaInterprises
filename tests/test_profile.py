def test_get_profile_creates_on_first_call(client, headers):
    r = client.get("/api/goat/profile/me", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["xp"], int) and data["xp"] >= 0
    assert data["level"] >= 1
    assert data["goat_tokens"] >= 100   # welcome bonus + any earned
    assert isinstance(data["quests_completed"], int)


def test_update_profile_username(client, headers):
    r = client.post("/api/goat/profile/me", json={"username": "elgoat"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["username"] == "elgoat"


def test_update_profile_username_taken(client, headers, headers2):
    client.post("/api/goat/profile/me", json={"username": "elgoat"}, headers=headers)
    r = client.post("/api/goat/profile/me", json={"username": "elgoat"}, headers=headers2)
    assert r.status_code == 400


def test_leaderboard_returns_list(client, headers):
    r = client.get("/api/goat/profile/leaderboard", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_token_balance(client, headers):
    r = client.get("/api/goat/tokens/balance", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "goat_tokens" in data
    assert "xp" in data
    assert "level" in data
