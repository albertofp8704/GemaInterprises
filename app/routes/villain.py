from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db, User
from ..auth import get_current_user
from ..models_goat import VillainArc, PlayerProfile, TokenTransaction
from .profile import _get_or_create_profile

router = APIRouter(prefix="/api/goat/villain", tags=["villain-arc"])


class VillainArcCreate(BaseModel):
    title: str
    quote: Optional[str] = None
    goals: List[str] = []
    end_date: Optional[datetime] = None


class VillainArcUpdate(BaseModel):
    quote: Optional[str] = None
    goals: Optional[List[str]] = None


CHECKIN_XP     = 30
CHECKIN_TOKENS = 5
POWER_UP_AT    = [7, 14, 21, 30, 60, 90]   # days → power level milestones


@router.get("/active")
async def get_active_villain_arc(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    arc = db.query(VillainArc).filter(
        VillainArc.user_id == current_user.id,
        VillainArc.status == "active",
    ).first()
    if not arc:
        return {"active": False}
    return {"active": True, **_serialize_arc(arc)}


@router.post("/start")
async def start_villain_arc(
    body: VillainArcCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(VillainArc).filter(
        VillainArc.user_id == current_user.id,
        VillainArc.status == "active",
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already in a Villain Arc. Complete it first.")

    arc = VillainArc(
        user_id=current_user.id,
        title=body.title,
        quote=body.quote,
        goals=body.goals,
        end_date=body.end_date,
    )
    db.add(arc)

    profile = _get_or_create_profile(current_user.id, db)
    profile.villain_arc_active = True

    tx = TokenTransaction(
        user_id=current_user.id,
        amount=25,
        type="villain_arc_start",
        description=f"Villain Arc activated: {body.title} 😈",
    )
    db.add(tx)
    profile.goat_tokens += 25
    db.commit()
    db.refresh(arc)

    return {"message": "Villain Arc activated 😈", **_serialize_arc(arc)}


@router.post("/{arc_id}/checkin")
async def daily_checkin(
    arc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    arc = db.query(VillainArc).filter(
        VillainArc.id == arc_id,
        VillainArc.user_id == current_user.id,
        VillainArc.status == "active",
    ).first()
    if not arc:
        raise HTTPException(status_code=404, detail="Active Villain Arc not found")

    arc.streak_days += 1

    # level up at milestones
    new_level = sum(1 for milestone in POWER_UP_AT if arc.streak_days >= milestone) + 1
    arc.power_level = new_level

    profile = _get_or_create_profile(current_user.id, db)
    profile.xp += CHECKIN_XP
    profile.goat_tokens += CHECKIN_TOKENS

    tx = TokenTransaction(
        user_id=current_user.id,
        amount=CHECKIN_TOKENS,
        type="villain_reward",
        description=f"Day {arc.streak_days} check-in 😈",
        ref_id=arc.id,
    )
    db.add(tx)
    db.commit()

    return {
        "streak_days": arc.streak_days,
        "power_level": arc.power_level,
        "xp_earned":   CHECKIN_XP,
        "tokens_earned": CHECKIN_TOKENS,
    }


@router.post("/{arc_id}/complete")
async def complete_villain_arc(
    arc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    arc = db.query(VillainArc).filter(
        VillainArc.id == arc_id,
        VillainArc.user_id == current_user.id,
        VillainArc.status == "active",
    ).first()
    if not arc:
        raise HTTPException(status_code=404, detail="Active Villain Arc not found")

    arc.status       = "completed"
    arc.completed_at = datetime.utcnow()

    # Completion bonus scales with streak
    bonus_tokens = arc.streak_days * 5 + arc.power_level * 20
    bonus_xp     = arc.streak_days * 10

    profile = _get_or_create_profile(current_user.id, db)
    profile.villain_arc_active = False
    profile.goat_tokens += bonus_tokens
    profile.xp += bonus_xp

    tx = TokenTransaction(
        user_id=current_user.id,
        amount=bonus_tokens,
        type="villain_arc_complete",
        description=f"Villain Arc completed: {arc.title} 🏆",
        ref_id=arc.id,
    )
    db.add(tx)
    db.commit()

    return {
        "message":     "Villain Arc completed! You leveled up. 🏆",
        "bonus_tokens": bonus_tokens,
        "bonus_xp":    bonus_xp,
        "final_streak": arc.streak_days,
        "final_power":  arc.power_level,
    }


@router.patch("/{arc_id}")
async def update_villain_arc(
    arc_id: int,
    body: VillainArcUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    arc = db.query(VillainArc).filter(
        VillainArc.id == arc_id,
        VillainArc.user_id == current_user.id,
    ).first()
    if not arc:
        raise HTTPException(status_code=404, detail="Villain Arc not found")
    if body.quote is not None:
        arc.quote = body.quote
    if body.goals is not None:
        arc.goals = body.goals
    db.commit()
    return _serialize_arc(arc)


def _serialize_arc(arc: VillainArc) -> dict:
    return {
        "id":          arc.id,
        "title":       arc.title,
        "quote":       arc.quote,
        "goals":       arc.goals,
        "status":      arc.status,
        "streak_days": arc.streak_days,
        "power_level": arc.power_level,
        "start_date":  arc.start_date.isoformat(),
        "end_date":    arc.end_date.isoformat() if arc.end_date else None,
        "completed_at": arc.completed_at.isoformat() if arc.completed_at else None,
    }
