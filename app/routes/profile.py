from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db, User
from ..auth import get_current_user
from ..models_goat import PlayerProfile, TokenTransaction

router = APIRouter(prefix="/api/goat/profile", tags=["profile"])


class ProfileCreate(BaseModel):
    username: str
    avatar_url: Optional[str] = None


class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[str] = None


def _get_or_create_profile(user_id: int, db: Session) -> PlayerProfile:
    profile = db.query(PlayerProfile).filter(PlayerProfile.user_id == user_id).first()
    if not profile:
        profile = PlayerProfile(user_id=user_id)
        db.add(profile)
        # Welcome bonus
        tx = TokenTransaction(
            user_id=user_id, amount=100, type="welcome_bonus",
            description="Welcome to GOAT Arc 🏆"
        )
        db.add(tx)
        db.commit()
        db.refresh(profile)
    return profile


def _xp_to_level(xp: int) -> int:
    """Each level requires 500 XP more than the previous."""
    level = 1
    threshold = 500
    while xp >= threshold:
        xp -= threshold
        level += 1
        threshold += 500
    return level


def _serialize_profile(profile: PlayerProfile) -> dict:
    accuracy = 0.0
    if profile.predictions_made > 0:
        accuracy = round(profile.predictions_correct / profile.predictions_made * 100, 1)
    return {
        "user_id":           profile.user_id,
        "username":          profile.username,
        "avatar_url":        profile.avatar_url,
        "xp":                profile.xp,
        "level":             profile.level,
        "gut_score":         accuracy,
        "goat_tokens":       profile.goat_tokens,
        "villain_arc_active": profile.villain_arc_active,
        "quests_completed":  profile.quests_completed,
        "predictions_made":  profile.predictions_made,
        "predictions_correct": profile.predictions_correct,
        "legacies_dropped":  profile.legacies_dropped,
        "legacies_found":    profile.legacies_found,
        "current_streak":    profile.current_streak,
        "longest_streak":    profile.longest_streak,
    }


@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(current_user.id, db)
    return _serialize_profile(profile)


@router.post("/me")
async def create_or_update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(current_user.id, db)
    if body.username is not None:
        existing = db.query(PlayerProfile).filter(
            PlayerProfile.username == body.username,
            PlayerProfile.user_id != current_user.id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        profile.username = body.username
    if body.avatar_url is not None:
        profile.avatar_url = body.avatar_url
    db.commit()
    db.refresh(profile)
    return _serialize_profile(profile)


@router.get("/leaderboard")
async def leaderboard(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    top = (
        db.query(PlayerProfile)
        .filter(PlayerProfile.username.isnot(None))
        .order_by(PlayerProfile.xp.desc())
        .limit(20)
        .all()
    )
    return [_serialize_profile(p) for p in top]
