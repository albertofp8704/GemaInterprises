def test_no_active_arc_on_fresh_user(client, headers2):
    r = client.get("/api/goat/villain/active", headers=headers2)
    assert r.status_code == 200
    assert r.json()["active"] is False


def test_start_villain_arc(client, headers2):
    r = client.post("/api/goat/villain/start", json={
        "title": "Mi mejor era",
        "quote": "Sin excusas",
        "goals": ["Terminar el proyecto", "Entrenar 5 días/semana"],
    }, headers=headers2)
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Mi mejor era"
    assert data["streak_days"] == 0
    assert data["power_level"] == 1
    assert len(data["goals"]) == 2


def test_active_arc_returns_after_start(client, headers2):
    r = client.get("/api/goat/villain/active", headers=headers2)
    assert r.status_code == 200
    data = r.json()
    assert data["active"] is True
    assert "id" in data


def test_start_second_arc_while_active_fails(client, headers2):
    r = client.post("/api/goat/villain/start", json={
        "title": "Otro arc",
        "goals": [],
    }, headers=headers2)
    assert r.status_code == 400


def test_villain_checkin_increments_streak(client, headers2):
    arc = client.get("/api/goat/villain/active", headers=headers2).json()
    arc_id = arc["id"]
    before_tokens = client.get("/api/goat/tokens/balance", headers=headers2).json()["goat_tokens"]

    r = client.post(f"/api/goat/villain/{arc_id}/checkin", headers=headers2)
    assert r.status_code == 200
    data = r.json()
    assert data["streak_days"] == 1
    assert data["power_level"] >= 1
    assert data["tokens_earned"] > 0

    after_tokens = client.get("/api/goat/tokens/balance", headers=headers2).json()["goat_tokens"]
    assert after_tokens > before_tokens


def test_complete_villain_arc(client, headers2):
    arc = client.get("/api/goat/villain/active", headers=headers2).json()
    arc_id = arc["id"]

    r = client.post(f"/api/goat/villain/{arc_id}/complete", headers=headers2)
    assert r.status_code == 200
    data = r.json()
    assert "bonus_tokens" in data
    assert data["bonus_tokens"] >= 0

    # Arc should no longer be active
    r2 = client.get("/api/goat/villain/active", headers=headers2)
    assert r2.json()["active"] is False
