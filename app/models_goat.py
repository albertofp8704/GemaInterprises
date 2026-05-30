from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Float,
    ForeignKey, Text, JSON, Date,
)
from datetime import datetime
from .database import Base


class PlayerProfile(Base):
    __tablename__ = "player_profiles"
    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    username            = Column(String(50), unique=True, nullable=True)
    avatar_url          = Column(String, nullable=True)
    xp                  = Column(Integer, default=0)
    level               = Column(Integer, default=1)
    gut_score           = Column(Float, default=0.0)       # prediction accuracy %
    goat_tokens         = Column(Integer, default=100)     # in-app currency
    villain_arc_active  = Column(Boolean, default=False)
    quests_completed    = Column(Integer, default=0)
    predictions_made    = Column(Integer, default=0)
    predictions_correct = Column(Integer, default=0)
    legacies_dropped    = Column(Integer, default=0)
    legacies_found      = Column(Integer, default=0)
    longest_streak      = Column(Integer, default=0)
    current_streak      = Column(Integer, default=0)
    last_quest_date     = Column(Date, nullable=True)
    created_at          = Column(DateTime, default=datetime.utcnow)
    updated_at          = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Campaign(Base):
    """Era Tracker — a defined chapter of the user's life."""
    __tablename__ = "campaigns"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    title       = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    emoji       = Column(String(10), default="⚽")
    start_date  = Column(DateTime, default=datetime.utcnow)
    end_date    = Column(DateTime, nullable=True)
    status      = Column(String(20), default="active")   # active | completed | abandoned
    goals       = Column(JSON, default=list)
    cover_color = Column(String(7), default="#1a1a2e")
    created_at  = Column(DateTime, default=datetime.utcnow)


class Quest(Base):
    """NPC daily missions."""
    __tablename__ = "quests"
    id             = Column(Integer, primary_key=True, index=True)
    title          = Column(String(200), nullable=False)
    description    = Column(Text, nullable=False)
    xp_reward      = Column(Integer, default=50)
    token_reward   = Column(Integer, default=10)
    category       = Column(String(50), default="social")  # social|personal|football|career|creative
    difficulty     = Column(String(20), default="normal")  # easy|normal|hard|legendary
    football_theme = Column(Boolean, default=False)
    available_date = Column(Date, nullable=True)   # null = always in pool
    is_daily       = Column(Boolean, default=True)
    created_at     = Column(DateTime, default=datetime.utcnow)


class UserQuest(Base):
    __tablename__ = "user_quests"
    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    quest_id      = Column(Integer, ForeignKey("quests.id"), nullable=False)
    completed_at  = Column(DateTime, default=datetime.utcnow)
    reflection    = Column(Text, nullable=True)
    xp_earned     = Column(Integer, default=0)
    tokens_earned = Column(Integer, default=0)


class WorldCupMatch(Base):
    __tablename__ = "worldcup_matches"
    id           = Column(Integer, primary_key=True, index=True)
    match_number = Column(Integer, nullable=True)
    team_home    = Column(String(50), nullable=False)
    team_away    = Column(String(50), nullable=False)
    flag_home    = Column(String(10), nullable=True)
    flag_away    = Column(String(10), nullable=True)
    match_date   = Column(DateTime, nullable=False)
    stadium      = Column(String(100), nullable=True)
    city         = Column(String(50), nullable=True)
    country      = Column(String(50), nullable=True)
    stage        = Column(String(30), default="group")   # group|r32|r16|qf|sf|final
    group_name   = Column(String(5), nullable=True)
    score_home   = Column(Integer, nullable=True)
    score_away   = Column(Integer, nullable=True)
    status       = Column(String(20), default="upcoming")  # upcoming|live|finished


class Prediction(Base):
    """Gut Feeling — match or life predictions."""
    __tablename__ = "predictions"
    id                = Column(Integer, primary_key=True, index=True)
    user_id           = Column(Integer, ForeignKey("users.id"), nullable=False)
    type              = Column(String(20), default="match")   # match | life
    match_id          = Column(Integer, ForeignKey("worldcup_matches.id"), nullable=True)
    predicted_home    = Column(Integer, nullable=True)
    predicted_away    = Column(Integer, nullable=True)
    description       = Column(Text, nullable=True)
    predicted_outcome = Column(String(200), nullable=True)
    is_correct        = Column(Boolean, nullable=True)
    points_earned     = Column(Integer, default=0)
    created_at        = Column(DateTime, default=datetime.utcnow)
    resolved_at       = Column(DateTime, nullable=True)


class VillainArc(Base):
    __tablename__ = "villain_arcs"
    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    title        = Column(String(100), nullable=False)
    quote        = Column(String(200), nullable=True)   # personal mantra
    start_date   = Column(DateTime, default=datetime.utcnow)
    end_date     = Column(DateTime, nullable=True)
    status       = Column(String(20), default="active")  # active|completed|abandoned
    goals        = Column(JSON, default=list)
    power_level  = Column(Integer, default=1)
    streak_days  = Column(Integer, default=0)
    completed_at = Column(DateTime, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)


class Legacy(Base):
    """Micro-Legacy — geo-tagged drops for strangers to find."""
    __tablename__ = "legacies"
    id                = Column(Integer, primary_key=True, index=True)
    user_id           = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_type      = Column(String(20), default="text")   # text|voice|image
    content           = Column(Text, nullable=False)
    lat               = Column(Float, nullable=False)
    lng               = Column(Float, nullable=False)
    location_name     = Column(String(200), nullable=True)
    city              = Column(String(100), nullable=True)
    country           = Column(String(100), nullable=True)
    found_count       = Column(Integer, default=0)
    is_active         = Column(Boolean, default=True)
    created_at        = Column(DateTime, default=datetime.utcnow)
    expires_at        = Column(DateTime, nullable=True)
    is_nft            = Column(Boolean, default=False)
    nft_token_id      = Column(String, nullable=True)
    mint_price_tokens = Column(Integer, nullable=True)


class TokenTransaction(Base):
    """GOAT Token economy ledger."""
    __tablename__ = "token_transactions"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount      = Column(Integer, nullable=False)   # positive=earn, negative=spend
    type        = Column(String(50), nullable=False)
    # quest_reward|prediction_reward|purchase|nft_mint|flashcard_buy|villain_reward
    description = Column(String(200), nullable=True)
    ref_id      = Column(Integer, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)


class FlashCard(Base):
    """Collectible tactical / player cards purchasable with GOAT tokens."""
    __tablename__ = "flash_cards"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    rarity      = Column(String(20), default="common")  # common|rare|epic|legendary
    card_type   = Column(String(30), default="player")  # player|tactic|stadium|moment
    image_url   = Column(String, nullable=True)
    token_price  = Column(Integer, default=50)
    supply       = Column(Integer, nullable=True)   # null = unlimited
    minted       = Column(Integer, default=0)
    card_metadata = Column(JSON, default=dict)
    created_at  = Column(DateTime, default=datetime.utcnow)


class UserFlashCard(Base):
    __tablename__ = "user_flash_cards"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    card_id     = Column(Integer, ForeignKey("flash_cards.id"), nullable=False)
    acquired_at = Column(DateTime, default=datetime.utcnow)
    is_nft      = Column(Boolean, default=False)
    nft_token_id = Column(String, nullable=True)
