from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db, User
from ..auth import get_current_user
from ..models_goat import TokenTransaction, FlashCard, UserFlashCard, PlayerProfile
from .profile import _get_or_create_profile
from fastapi import HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/goat/tokens", tags=["tokens"])


@router.get("/balance")
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _get_or_create_profile(current_user.id, db)
    return {"goat_tokens": profile.goat_tokens, "xp": profile.xp, "level": profile.level}


@router.get("/history")
async def token_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txs = (
        db.query(TokenTransaction)
        .filter(TokenTransaction.user_id == current_user.id)
        .order_by(TokenTransaction.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "amount":      tx.amount,
            "type":        tx.type,
            "description": tx.description,
            "created_at":  tx.created_at.isoformat(),
        }
        for tx in txs
    ]


# ── Flash Cards ─────────────────────────────────────────────────────────────

@router.get("/flashcards")
async def list_flashcards(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cards = db.query(FlashCard).order_by(FlashCard.rarity.desc()).all()
    return [_serialize_card(c) for c in cards]


@router.post("/flashcards/{card_id}/buy")
async def buy_flashcard(
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = db.query(FlashCard).filter(FlashCard.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if card.supply and card.minted >= card.supply:
        raise HTTPException(status_code=400, detail="Card sold out")

    already_owned = db.query(UserFlashCard).filter(
        UserFlashCard.user_id == current_user.id,
        UserFlashCard.card_id == card_id,
    ).first()
    if already_owned:
        raise HTTPException(status_code=400, detail="Already own this card")

    profile = _get_or_create_profile(current_user.id, db)
    if profile.goat_tokens < card.token_price:
        raise HTTPException(status_code=400, detail=f"Need {card.token_price} GOAT tokens")

    profile.goat_tokens -= card.token_price
    card.minted += 1

    user_card = UserFlashCard(user_id=current_user.id, card_id=card_id)
    db.add(user_card)

    tx = TokenTransaction(
        user_id=current_user.id,
        amount=-card.token_price,
        type="flashcard_buy",
        description=f"Bought Flash Card: {card.name} ({card.rarity})",
        ref_id=card.id,
    )
    db.add(tx)
    db.commit()

    return {
        "message":          f"You now own '{card.name}' 🃏",
        "tokens_spent":     card.token_price,
        "remaining_tokens": profile.goat_tokens,
    }


@router.get("/flashcards/mine")
async def my_flashcards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owned = (
        db.query(UserFlashCard, FlashCard)
        .join(FlashCard, UserFlashCard.card_id == FlashCard.id)
        .filter(UserFlashCard.user_id == current_user.id)
        .all()
    )
    return [
        {**_serialize_card(card), "acquired_at": uc.acquired_at.isoformat(), "is_nft": uc.is_nft}
        for uc, card in owned
    ]


def _serialize_card(c: FlashCard) -> dict:
    return {
        "id":          c.id,
        "name":        c.name,
        "description": c.description,
        "rarity":      c.rarity,
        "card_type":   c.card_type,
        "image_url":   c.image_url,
        "token_price": c.token_price,
        "supply":      c.supply,
        "minted":      c.minted,
        "metadata":    c.metadata,
    }
