def test_token_history_returns_transactions(client, headers):
    r = client.get("/api/goat/tokens/history", headers=headers)
    assert r.status_code == 200
    history = r.json()
    assert isinstance(history, list)
    # Welcome bonus should be in history
    types = [tx["type"] for tx in history]
    assert "welcome_bonus" in types


def test_flashcard_shop_lists_cards(client, headers):
    r = client.get("/api/goat/tokens/flashcards", headers=headers)
    assert r.status_code == 200
    cards = r.json()
    assert isinstance(cards, list)
    if cards:
        card = cards[0]
        assert "name" in card
        assert "rarity" in card
        assert "token_price" in card


def test_buy_flashcard_deducts_tokens(client, headers):
    cards = client.get("/api/goat/tokens/flashcards", headers=headers).json()
    if not cards:
        return

    # Find an affordable card
    balance = client.get("/api/goat/tokens/balance", headers=headers).json()["goat_tokens"]
    card = next((c for c in cards if c["token_price"] <= balance), None)
    if not card:
        return

    r = client.post(f"/api/goat/tokens/flashcards/{card['id']}/buy", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["tokens_spent"] == card["token_price"]
    assert data["remaining_tokens"] == balance - card["token_price"]


def test_buy_same_flashcard_twice_fails(client, headers):
    cards = client.get("/api/goat/tokens/flashcards", headers=headers).json()
    my_cards = client.get("/api/goat/tokens/flashcards/mine", headers=headers).json()
    if not my_cards:
        return

    owned_id = my_cards[0]["id"]
    r = client.post(f"/api/goat/tokens/flashcards/{owned_id}/buy", headers=headers)
    assert r.status_code == 400


def test_my_flashcards_shows_collection(client, headers):
    r = client.get("/api/goat/tokens/flashcards/mine", headers=headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_campaign_lifecycle(client, headers):
    # Create campaign
    r = client.post("/api/goat/campaigns/", json={
        "title": "Era 2026",
        "description": "Mi mejor año",
        "emoji": "🏆",
        "goals": ["Lanzar la app", "Conseguir 1000 usuarios"],
    }, headers=headers)
    assert r.status_code == 200
    campaign = r.json()
    assert campaign["title"] == "Era 2026"
    assert campaign["status"] == "active"
    cid = campaign["id"]

    # List campaigns
    r2 = client.get("/api/goat/campaigns/", headers=headers)
    assert any(c["id"] == cid for c in r2.json())

    # Update campaign
    r3 = client.patch(f"/api/goat/campaigns/{cid}", json={"emoji": "🚀"}, headers=headers)
    assert r3.status_code == 200
    assert r3.json()["emoji"] == "🚀"

    # Complete campaign
    r4 = client.post(f"/api/goat/campaigns/{cid}/complete", headers=headers)
    assert r4.status_code == 200
    assert "bonus_tokens" in r4.json()

    # Verify status
    r5 = client.get(f"/api/goat/campaigns/{cid}", headers=headers)
    assert r5.json()["status"] == "completed"
