import httpx
import os

BASE_URL = (
    os.getenv("GOAT_API_URL") or
    "https://gemainterprises-production-a30b.up.railway.app"
)


class APIError(Exception):
    def __init__(self, message: str, status: int = 0):
        super().__init__(message)
        self.status = status


class APIClient:
    def __init__(self):
        self.token: str | None = None
        self.base = BASE_URL.rstrip("/")

    def _h(self):
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _req(self, method, path, **kwargs):
        try:
            r = httpx.request(method, f"{self.base}{path}", headers=self._h(), timeout=15, **kwargs)
        except httpx.ConnectError:
            raise APIError("No se puede conectar al servidor", 0)
        if not r.is_success:
            try:
                detail = r.json().get("detail", r.text)
            except Exception:
                detail = r.text
            raise APIError(str(detail), r.status_code)
        return r.json() if r.text else {}

    # ── Auth ─────────────────────────────────────────────────────────────────
    def register(self, email: str, password: str) -> dict:
        data = self._req("POST", "/api/auth/register", json={"email": email, "password": password})
        self.token = data["token"]
        return data

    def login(self, email: str, password: str) -> dict:
        data = self._req("POST", "/api/auth/login", json={"email": email, "password": password})
        self.token = data["token"]
        return data

    def me(self) -> dict:
        return self._req("GET", "/api/auth/me")

    # ── Profile ──────────────────────────────────────────────────────────────
    def get_profile(self) -> dict:
        return self._req("GET", "/api/goat/profile/me")

    def update_profile(self, username: str = None, avatar_url: str = None) -> dict:
        body = {}
        if username:
            body["username"] = username
        if avatar_url:
            body["avatar_url"] = avatar_url
        return self._req("POST", "/api/goat/profile/me", json=body)

    def leaderboard(self) -> list:
        return self._req("GET", "/api/goat/profile/leaderboard")

    # ── Quests ───────────────────────────────────────────────────────────────
    def today_quests(self) -> list:
        return self._req("GET", "/api/goat/quests/today")

    def complete_quest(self, quest_id: int, reflection: str = None) -> dict:
        return self._req("POST", f"/api/goat/quests/{quest_id}/complete", json={"reflection": reflection})

    def quest_history(self) -> list:
        return self._req("GET", "/api/goat/quests/history")

    # ── Predictions ──────────────────────────────────────────────────────────
    def matches(self, status="upcoming") -> list:
        return self._req("GET", f"/api/goat/predictions/matches?status={status}")

    def predict_match(self, match_id: int, home: int, away: int) -> dict:
        return self._req("POST", "/api/goat/predictions/match",
                         json={"match_id": match_id, "predicted_home": home, "predicted_away": away})

    def predict_life(self, description: str, outcome: str) -> dict:
        return self._req("POST", "/api/goat/predictions/life",
                         json={"description": description, "predicted_outcome": outcome})

    def my_predictions(self) -> list:
        return self._req("GET", "/api/goat/predictions/mine")

    def prediction_leaderboard(self) -> list:
        return self._req("GET", "/api/goat/predictions/leaderboard")

    # ── Villain Arc ──────────────────────────────────────────────────────────
    def active_villain_arc(self) -> dict:
        return self._req("GET", "/api/goat/villain/active")

    def start_villain_arc(self, title: str, quote: str = None, goals: list = None) -> dict:
        return self._req("POST", "/api/goat/villain/start",
                         json={"title": title, "quote": quote, "goals": goals or []})

    def villain_checkin(self, arc_id: int) -> dict:
        return self._req("POST", f"/api/goat/villain/{arc_id}/checkin")

    def complete_villain_arc(self, arc_id: int) -> dict:
        return self._req("POST", f"/api/goat/villain/{arc_id}/complete")

    # ── Campaigns ────────────────────────────────────────────────────────────
    def campaigns(self) -> list:
        return self._req("GET", "/api/goat/campaigns/")

    def create_campaign(self, title: str, description: str = None, emoji: str = "⚽", goals: list = None) -> dict:
        return self._req("POST", "/api/goat/campaigns/",
                         json={"title": title, "description": description, "emoji": emoji, "goals": goals or []})

    def complete_campaign(self, campaign_id: int) -> dict:
        return self._req("POST", f"/api/goat/campaigns/{campaign_id}/complete")

    # ── Legacy ───────────────────────────────────────────────────────────────
    def nearby_legacies(self, lat: float, lng: float, radius: float = 2.0) -> list:
        return self._req("GET", f"/api/goat/legacies/nearby?lat={lat}&lng={lng}&radius_km={radius}")

    def drop_legacy(self, content: str, lat: float, lng: float,
                    content_type: str = "text", city: str = None, country: str = None) -> dict:
        return self._req("POST", "/api/goat/legacies/drop",
                         json={"content": content, "lat": lat, "lng": lng,
                               "content_type": content_type, "city": city, "country": country})

    def find_legacy(self, legacy_id: int) -> dict:
        return self._req("POST", f"/api/goat/legacies/find/{legacy_id}")

    def my_legacies(self) -> list:
        return self._req("GET", "/api/goat/legacies/mine")

    # ── Tokens & Flash Cards ─────────────────────────────────────────────────
    def token_balance(self) -> dict:
        return self._req("GET", "/api/goat/tokens/balance")

    def token_history(self) -> list:
        return self._req("GET", "/api/goat/tokens/history")

    def flashcards(self) -> list:
        return self._req("GET", "/api/goat/tokens/flashcards")

    def sync_flashcard_images(self) -> dict:
        try:
            return self._req("POST", "/api/goat/tokens/flashcards/sync-images")
        except APIError:
            return {}

    def buy_flashcard(self, card_id: int) -> dict:
        return self._req("POST", f"/api/goat/tokens/flashcards/{card_id}/buy")

    def my_flashcards(self) -> list:
        return self._req("GET", "/api/goat/tokens/flashcards/mine")

    # ── Wallet ───────────────────────────────────────────────────────────────
    def wallet_challenge(self) -> dict:
        return self._req("GET", "/api/wallet/challenge")

    def wallet_connect(self, wallet_address: str, signature: str) -> dict:
        return self._req("POST", "/api/wallet/connect",
                         json={"wallet_address": wallet_address, "signature": signature})

    def wallet_status(self) -> dict:
        return self._req("GET", "/api/wallet/status")

    def mint_tokens_onchain(self, amount: int) -> dict:
        return self._req("POST", "/api/wallet/mint-tokens", json={"amount_tokens": amount})

    def mint_legacy_nft(self, legacy_id: int, token_uri: str) -> dict:
        return self._req("POST", "/api/wallet/mint-legacy-nft",
                         json={"legacy_id": legacy_id, "token_uri": token_uri})

    def mint_flashcard_nft(self, user_flashcard_id: int) -> dict:
        return self._req("POST", "/api/wallet/mint-flashcard",
                         json={"user_flashcard_id": user_flashcard_id})
