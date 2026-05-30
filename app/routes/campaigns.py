from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db, User
from ..auth import get_current_user
from ..models_goat import Campaign, PlayerProfile, TokenTransaction
from .profile import _get_or_create_profile

router = APIRouter(prefix="/api/goat/campaigns", tags=["campaigns"])


class CampaignCreate(BaseModel):
    title:       str
    description: Optional[str] = None
    emoji:       Optional[str] = "⚽"
    goals:       List[str] = []
    cover_color: Optional[str] = "#1a1a2e"
    end_date:    Optional[datetime] = None


class CampaignUpdate(BaseModel):
    title:       Optional[str] = None
    description: Optional[str] = None
    emoji:       Optional[str] = None
    goals:       Optional[List[str]] = None
    cover_color: Optional[str] = None


@router.get("/")
async def list_campaigns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    campaigns = (
        db.query(Campaign)
        .filter(Campaign.user_id == current_user.id)
        .order_by(Campaign.created_at.desc())
        .all()
    )
    return [_serialize(c) for c in campaigns]


@router.post("/")
async def create_campaign(
    body: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    active_count = db.query(Campaign).filter(
        Campaign.user_id == current_user.id,
        Campaign.status == "active",
    ).count()
    if active_count >= 3:
        raise HTTPException(status_code=400, detail="Max 3 active campaigns at once")

    c = Campaign(
        user_id=current_user.id,
        title=body.title,
        description=body.description,
        emoji=body.emoji,
        goals=body.goals,
        cover_color=body.cover_color,
        end_date=body.end_date,
    )
    db.add(c)

    profile = _get_or_create_profile(current_user.id, db)
    profile.goat_tokens += 10

    tx = TokenTransaction(
        user_id=current_user.id,
        amount=10,
        type="campaign_create",
        description=f"New era started: {body.title} {body.emoji}",
    )
    db.add(tx)
    db.commit()
    db.refresh(c)

    return _serialize(c)


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _serialize(c)


@router.patch("/{campaign_id}")
async def update_campaign(
    campaign_id: int,
    body: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Campaign not found")
    for field, value in body.dict(exclude_none=True).items():
        setattr(c, field, value)
    db.commit()
    return _serialize(c)


@router.post("/{campaign_id}/complete")
async def complete_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    c = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id,
        Campaign.status == "active",
    ).first()
    if not c:
        raise HTTPException(status_code=404, detail="Active campaign not found")

    c.status   = "completed"
    c.end_date = datetime.utcnow()

    profile = _get_or_create_profile(current_user.id, db)
    bonus = 50 + len(c.goals or []) * 10
    profile.goat_tokens += bonus
    profile.xp += 200

    tx = TokenTransaction(
        user_id=current_user.id,
        amount=bonus,
        type="campaign_complete",
        description=f"Era completed: {c.title} {c.emoji} 🏆",
        ref_id=c.id,
    )
    db.add(tx)
    db.commit()

    return {"message": f"Era '{c.title}' completed! 🏆", "bonus_tokens": bonus, "xp_earned": 200}


def _serialize(c: Campaign) -> dict:
    return {
        "id":          c.id,
        "title":       c.title,
        "description": c.description,
        "emoji":       c.emoji,
        "goals":       c.goals,
        "cover_color": c.cover_color,
        "status":      c.status,
        "start_date":  c.start_date.isoformat(),
        "end_date":    c.end_date.isoformat() if c.end_date else None,
        "created_at":  c.created_at.isoformat(),
    }
