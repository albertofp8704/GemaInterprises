def test_today_quests_returns_list(client, headers):
    r = client.get("/api/goat/quests/today", headers=headers)
    assert r.status_code == 200
    quests = r.json()
    assert isinstance(quests, list)
    # seed_goat runs on startup — quests should be there
    if quests:
        q = quests[0]
        assert "id" in q
        assert "title" in q
        assert "xp_reward" in q
        assert "token_reward" in q
        assert "completed" in q


def test_complete_quest_awards_xp_and_tokens(client, headers):
    quests = client.get("/api/goat/quests/today", headers=headers).json()
    if not quests:
        return  # nothing to test without seed data

    quest = next((q for q in quests if not q["completed"]), None)
    if not quest:
        return

    before = client.get("/api/goat/profile/me", headers=headers).json()

    r = client.post(
        f"/api/goat/quests/{quest['id']}/complete",
        json={"reflection": "Fue genial"},
        headers=headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["xp_earned"] > 0
    assert data["tokens_earned"] > 0
    assert data["current_streak"] >= 1

    after = client.get("/api/goat/profile/me", headers=headers).json()
    assert after["xp"] > before["xp"]
    assert after["goat_tokens"] > before["goat_tokens"]
    assert after["quests_completed"] == before["quests_completed"] + 1


def test_complete_quest_twice_same_day_fails(client, headers):
    quests = client.get("/api/goat/quests/today", headers=headers).json()
    done = [q for q in quests if q.get("completed")]
    if not done:
        return  # need a completed quest

    r = client.post(
        f"/api/goat/quests/{done[0]['id']}/complete",
        json={},
        headers=headers,
    )
    assert r.status_code == 400


def test_quest_history(client, headers):
    r = client.get("/api/goat/quests/history", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
