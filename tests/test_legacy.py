LEGACY_CONTENT = "Esto lo escribe alguien que pasó por aquí en 2026."
LEGACY_LAT = 40.4168   # Madrid
LEGACY_LNG = -3.7038


def test_drop_legacy(client, headers):
    r = client.post("/api/goat/legacies/drop", json={
        "content": LEGACY_CONTENT,
        "lat": LEGACY_LAT,
        "lng": LEGACY_LNG,
        "city": "Madrid",
        "country": "España",
    }, headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "id" in data


def test_my_legacies_contains_drop(client, headers):
    r = client.get("/api/goat/legacies/mine", headers=headers)
    assert r.status_code == 200
    legacies = r.json()
    assert len(legacies) >= 1
    assert any(l["content"] == LEGACY_CONTENT for l in legacies)


def test_nearby_legacies_returns_results(client, headers2):
    # User2 looks near Madrid where user1 dropped one
    r = client.get(
        f"/api/goat/legacies/nearby?lat={LEGACY_LAT}&lng={LEGACY_LNG}&radius_km=1",
        headers=headers2,
    )
    assert r.status_code == 200
    nearby = r.json()
    assert isinstance(nearby, list)
    # Should find the drop we made (user1 != user2)
    assert len(nearby) >= 1
    # Distance should be near-zero
    assert nearby[0]["distance_km"] < 1.0


def test_find_legacy_reveals_content_and_rewards(client, headers2):
    # Get nearby legacy id
    nearby = client.get(
        f"/api/goat/legacies/nearby?lat={LEGACY_LAT}&lng={LEGACY_LNG}&radius_km=1",
        headers=headers2,
    ).json()
    assert nearby, "No nearby legacies to find"

    legacy_id = nearby[0]["id"]
    before = client.get("/api/goat/tokens/balance", headers=headers2).json()["goat_tokens"]

    r = client.post(f"/api/goat/legacies/find/{legacy_id}", headers=headers2)
    assert r.status_code == 200
    data = r.json()
    assert data["content"] == LEGACY_CONTENT
    assert data["tokens_earned"] > 0

    after = client.get("/api/goat/tokens/balance", headers=headers2).json()["goat_tokens"]
    assert after > before


def test_cannot_find_own_legacy(client, headers):
    my_legacies = client.get("/api/goat/legacies/mine", headers=headers).json()
    assert my_legacies
    legacy_id = my_legacies[0]["id"]

    r = client.post(f"/api/goat/legacies/find/{legacy_id}", headers=headers)
    assert r.status_code == 400
