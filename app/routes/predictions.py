from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..database import get_db, User
from ..auth import get_current_user
from ..models_goat import Prediction, WorldCupMatch, PlayerProfile, TokenTransaction
from .profile import _get_or_create_profile

router = APIRouter(prefix="/api/goat/predictions", tags=["predictions"])

POINTS_EXACT_SCORE  = 10   # exact scoreline
POINTS_CORRECT_WINNER = 5  # correct winner / draw
TOKENS_EXACT_SCORE  = 20
TOKENS_CORRECT_WINNER = 10


class MatchPredictionBody(BaseModel):
    match_id:       int
    predicted_home: int
    predicted_away: int


class LifePredictionBody(BaseModel):
    description:       str
    predicted_outcome: str


@router.get("/matches")
async def list_matches(
    stage: Optional[str] = None,
    status: Optional[str] = "upcoming",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(WorldCupMatch)
    if stage:
        q = q.filter(WorldCupMatch.stage == stage)
    if status:
        q = q.filter(WorldCupMatch.status == status)
    matches = q.order_by(WorldCupMatch.match_date).all()
    return [_serialize_match(m) for m in matches]


@router.get("/matches/{match_id}")
async def get_match(
    match_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    m = db.query(WorldCupMatch).filter(WorldCupMatch.id == match_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    return _serialize_match(m)


@router.post("/match")
async def predict_match(
    body: MatchPredictionBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    match = db.query(WorldCupMatch).filter(WorldCupMatch.id == body.match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status != "upcoming":
        raise HTTPException(status_code=400, detail="Match already started or finished")

    existing = db.query(Prediction).filter(
        Prediction.user_id == current_user.id,
        Prediction.match_id == body.match_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already predicted this match")

    pred = Prediction(
        user_id=current_user.id,
        type="match",
        match_id=body.match_id,
        predicted_home=body.predicted_home,
        predicted_away=body.predicted_away,
    )
    db.add(pred)

    profile = _get_or_create_profile(current_user.id, db)
    profile.predictions_made += 1
    db.commit()
    db.refresh(pred)

    return {"id": pred.id, "message": "Prediction locked in 🔒"}


@router.post("/life")
async def predict_life(
    body: LifePredictionBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pred = Prediction(
        user_id=current_user.id,
        type="life",
        description=body.description,
        predicted_outcome=body.predicted_outcome,
    )
    db.add(pred)

    profile = _get_or_create_profile(current_user.id, db)
    profile.predictions_made += 1
    db.commit()
    db.refresh(pred)

    return {"id": pred.id, "message": "Life prediction saved 🔮"}


@router.get("/mine")
async def my_predictions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preds = (
        db.query(Prediction)
        .filter(Prediction.user_id == current_user.id)
        .order_by(Prediction.created_at.desc())
        .all()
    )
    return [_serialize_prediction(p) for p in preds]


@router.get("/leaderboard")
async def prediction_leaderboard(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    profiles = (
        db.query(PlayerProfile)
        .filter(PlayerProfile.predictions_made >= 3)
        .order_by(PlayerProfile.gut_score.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "username":           p.username,
            "gut_score":          p.gut_score,
            "predictions_made":   p.predictions_made,
            "predictions_correct": p.predictions_correct,
        }
        for p in profiles
    ]


# ── Internal: resolve match predictions ─────────────────────────────────────
@router.post("/matches/{match_id}/resolve")
async def resolve_match_predictions(
    match_id: int,
    db: Session = Depends(get_db),
):
    """Called internally after a match finishes to resolve all predictions."""
    match = db.query(WorldCupMatch).filter(WorldCupMatch.id == match_id).first()
    if not match or match.score_home is None:
        raise HTTPException(status_code=400, detail="Match result not set")

    preds = db.query(Prediction).filter(
        Prediction.match_id == match_id,
        Prediction.is_correct == None,
    ).all()

    resolved = 0
    for pred in preds:
        exact = (
            pred.predicted_home == match.score_home
            and pred.predicted_away == match.score_away
        )
        correct_winner = (
            (pred.predicted_home > pred.predicted_away) == (match.score_home > match.score_away)
            and (pred.predicted_home == pred.predicted_away) == (match.score_home == match.score_away)
        )

        if exact:
            pred.is_correct   = True
            pred.points_earned = POINTS_EXACT_SCORE
            token_reward       = TOKENS_EXACT_SCORE
        elif correct_winner:
            pred.is_correct   = True
            pred.points_earned = POINTS_CORRECT_WINNER
            token_reward       = TOKENS_CORRECT_WINNER
        else:
            pred.is_correct   = False
            pred.points_earned = 0
            token_reward       = 0

        pred.resolved_at = datetime.utcnow()

        profile = db.query(PlayerProfile).filter(PlayerProfile.user_id == pred.user_id).first()
        if profile:
            if pred.is_correct:
                profile.predictions_correct += 1
            if profile.predictions_made > 0:
                profile.gut_score = round(
                    profile.predictions_correct / profile.predictions_made * 100, 1
                )
            if token_reward > 0:
                profile.goat_tokens += token_reward
                tx = TokenTransaction(
                    user_id=pred.user_id,
                    amount=token_reward,
                    type="prediction_reward",
                    description=f"Correct prediction: {match.team_home} vs {match.team_away}",
                    ref_id=match.id,
                )
                db.add(tx)
        resolved += 1

    db.commit()
    return {"resolved": resolved}


def _serialize_match(m: WorldCupMatch) -> dict:
    return {
        "id":         m.id,
        "team_home":  m.team_home,
        "team_away":  m.team_away,
        "flag_home":  m.flag_home,
        "flag_away":  m.flag_away,
        "match_date": m.match_date.isoformat(),
        "stadium":    m.stadium,
        "city":       m.city,
        "country":    m.country,
        "stage":      m.stage,
        "group_name": m.group_name,
        "score_home": m.score_home,
        "score_away": m.score_away,
        "status":     m.status,
    }


def _serialize_prediction(p: Prediction) -> dict:
    return {
        "id":               p.id,
        "type":             p.type,
        "match_id":         p.match_id,
        "predicted_home":   p.predicted_home,
        "predicted_away":   p.predicted_away,
        "description":      p.description,
        "predicted_outcome": p.predicted_outcome,
        "is_correct":       p.is_correct,
        "points_earned":    p.points_earned,
        "created_at":       p.created_at.isoformat(),
        "resolved_at":      p.resolved_at.isoformat() if p.resolved_at else None,
    }
