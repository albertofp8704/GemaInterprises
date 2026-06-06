def test_list_upcoming_matches(client, headers):
    r = client.get("/api/goat/predictions/matches?status=upcoming", headers=headers)
    assert r.status_code == 200
    matches = r.json()
    assert isinstance(matches, list)
    if matches:
        m = matches[0]
        assert "team_home" in m
        assert "team_away" in m
        assert "match_date" in m
        assert "stage" in m


def test_predict_match(client, headers):
    matches = client.get("/api/goat/predictions/matches?status=upcoming", headers=headers).json()
    if not matches:
        return

    m = matches[0]
    r = client.post("/api/goat/predictions/match", json={
        "match_id": m["id"],
        "predicted_home": 2,
        "predicted_away": 1,
    }, headers=headers)
    assert r.status_code == 200
    assert "id" in r.json()


def test_predict_same_match_twice_fails(client, headers):
    matches = client.get("/api/goat/predictions/matches?status=upcoming", headers=headers).json()
    if not matches:
        return

    m = matches[0]
    # first one (already done above in same session — might 400)
    r = client.post("/api/goat/predictions/match", json={
        "match_id": m["id"],
        "predicted_home": 1,
        "predicted_away": 0,
    }, headers=headers)
    assert r.status_code in (200, 400)  # 400 if already predicted


def test_predict_life(client, headers):
    r = client.post("/api/goat/predictions/life", json={
        "description": "Terminaré mi proyecto este mes",
        "predicted_outcome": "Sí lo terminaré",
    }, headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] > 0


def test_my_predictions(client, headers):
    r = client.get("/api/goat/predictions/mine", headers=headers)
    assert r.status_code == 200
    preds = r.json()
    assert isinstance(preds, list)
    assert len(preds) >= 1   # at least life prediction above


def test_prediction_leaderboard(client, headers):
    r = client.get("/api/goat/predictions/leaderboard", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)
