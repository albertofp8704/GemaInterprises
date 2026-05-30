from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime

from ..database import get_db, User
from ..auth import get_current_user
from ..models_goat import Quest, UserQuest, PlayerProfile, TokenTransaction
from .profile import _get_or_create_profile, _xp_to_level

router = APIRouter(prefix="/api/goat/quests", tags=["quests"])


class CompleteQuestBody(BaseModel):
    reflection: Optional[str] = None


@router.get("/today")
async def get_today_quests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    completed_ids = {
        uq.quest_id
        for uq in db.query(UserQuest)
        .filter(
            UserQuest.user_id == current_user.id,
            UserQuest.completed_at >= datetime.combine(today, datetime.min.time()),
        )
        .all()
    }

    quests = (
        db.query(Quest)
        .filter(
            Quest.is_daily == True,
            (Quest.available_date == None) | (Quest.available_date == today),
        )
        .order_by(Quest.difficulty)
        .limit(5)
        .all()
    )

    return [
        {
            "id":             q.id,
            "title":          q.title,
            "description":    q.description,
            "xp_reward":      q.xp_reward,
            "token_reward":   q.token_reward,
            "category":       q.category,
            "difficulty":     q.difficulty,
            "football_theme": q.football_theme,
            "completed":      q.id in completed_ids,
        }
        for q in quests
    ]


@router.post("/{quest_id}/complete")
async def complete_quest(
    quest_id: int,
    body: CompleteQuestBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    quest = db.query(Quest).filter(Quest.id == quest_id).first()
    if not quest:
        raise HTTPException(status_code=404, detail="Quest not found")

    today = date.today()
    already_done = db.query(UserQuest).filter(
        UserQuest.user_id == current_user.id,
        UserQuest.quest_id == quest_id,
        UserQuest.completed_at >= datetime.combine(today, datetime.min.time()),
    ).first()
    if already_done:
        raise HTTPException(status_code=400, detail="Quest already completed today")

    uq = UserQuest(
        user_id=current_user.id,
        quest_id=quest_id,
        reflection=body.reflection,
        xp_earned=quest.xp_reward,
        tokens_earned=quest.token_reward,
    )
    db.add(uq)

    profile = _get_or_create_profile(current_user.id, db)
    profile.xp += quest.xp_reward
    profile.goat_tokens += quest.token_reward
    profile.quests_completed += 1
    profile.level = _xp_to_level(profile.xp)

    # streak logic
    yesterday = date.fromordinal(today.toordinal() - 1)
    if profile.last_quest_date == yesterday:
        profile.current_streak += 1
    elif profile.last_quest_date != today:
        profile.current_streak = 1
    if profile.current_streak > profile.longest_streak:
        profile.longest_streak = profile.current_streak
    profile.last_quest_date = today

    # villain arc power boost
    if profile.villain_arc_active:
        profile.xp += 25
        profile.goat_tokens += 5

    tx = TokenTransaction(
        user_id=current_user.id,
        amount=quest.token_reward,
        type="quest_reward",
        description=f"Quest completed: {quest.title}",
        ref_id=quest.id,
    )
    db.add(tx)
    db.commit()

    return {
        "message":        "Quest completed! 🏆",
        "xp_earned":      quest.xp_reward,
        "tokens_earned":  quest.token_reward,
        "new_xp":         profile.xp,
        "new_level":      profile.level,
        "current_streak": profile.current_streak,
        "goat_tokens":    profile.goat_tokens,
    }


@router.get("/history")
async def quest_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    history = (
        db.query(UserQuest, Quest)
        .join(Quest, UserQuest.quest_id == Quest.id)
        .filter(UserQuest.user_id == current_user.id)
        .order_by(UserQuest.completed_at.desc())
        .limit(30)
        .all()
    )
    return [
        {
            "quest_title": q.title,
            "category":    q.category,
            "difficulty":  q.difficulty,
            "xp_earned":   uq.xp_earned,
            "tokens_earned": uq.tokens_earned,
            "reflection":  uq.reflection,
            "completed_at": uq.completed_at.isoformat(),
        }
        for uq, q in history
    ]
