from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import math

from ..database import get_db, User
from ..auth import get_current_user
from ..models_goat import Legacy, PlayerProfile, TokenTransaction
from .profile import _get_or_create_profile

router = APIRouter(prefix="/api/goat/legacies", tags=["legacies"])

MAX_RADIUS_KM  = 5.0
FIND_XP        = 15
FIND_TOKENS    = 5
DROP_COST_FREE = 0
MINT_NFT_COST  = 200  # GOAT tokens to mint a legacy as NFT


class LegacyCreate(BaseModel):
    content:       str
    content_type:  Optional[str] = "text"
    lat:           float
    lng:           float
    location_name: Optional[str] = None
    city:          Optional[str] = None
    country:       Optional[str] = None
    expires_hours: Optional[int] = None   # null = permanent


class MintNFTBody(BaseModel):
    legacy_id: int


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


@router.get("/nearby")
async def get_nearby_legacies(
    lat: float,
    lng: float,
    radius_km: float = 2.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    radius_km = min(radius_km, MAX_RADIUS_KM)
    all_active = db.query(Legacy).filter(
        Legacy.is_active == True,
        Legacy.user_id != current_user.id,
        (Legacy.expires_at == None) | (Legacy.expires_at > datetime.utcnow()),
    ).all()

    nearby = [
        l for l in all_active
        if _haversine_km(lat, lng, l.lat, l.lng) <= radius_km
    ]

    return [
        {
            "id":            l.id,
            "content_type":  l.content_type,
            "lat":           l.lat,
            "lng":           l.lng,
            "location_name": l.location_name,
            "city":          l.city,
            "country":       l.country,
            "found_count":   l.found_count,
            "created_at":    l.created_at.isoformat(),
            "is_nft":        l.is_nft,
            "distance_km":   round(_haversine_km(lat, lng, l.lat, l.lng), 2),
        }
        for l in nearby
    ]


@router.post("/find/{legacy_id}")
async def find_legacy(
    legacy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    legacy = db.query(Legacy).filter(Legacy.id == legacy_id, Legacy.is_active == True).first()
    if not legacy:
        raise HTTPException(status_code=404, detail="Legacy not found or expired")
    if legacy.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You can't find your own legacy")

    legacy.found_count += 1

    profile = _get_or_create_profile(current_user.id, db)
    profile.legacies_found += 1
    profile.xp += FIND_XP
    profile.goat_tokens += FIND_TOKENS

    tx = TokenTransaction(
        user_id=current_user.id,
        amount=FIND_TOKENS,
        type="legacy_found",
        description=f"Found a legacy 📍",
        ref_id=legacy.id,
    )
    db.add(tx)
    db.commit()

    return {
        "content":       legacy.content,
        "content_type":  legacy.content_type,
        "location_name": legacy.location_name,
        "city":          legacy.city,
        "found_count":   legacy.found_count,
        "is_nft":        legacy.is_nft,
        "xp_earned":     FIND_XP,
        "tokens_earned": FIND_TOKENS,
    }


@router.post("/drop")
async def drop_legacy(
    body: LegacyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expires_at = None
    if body.expires_hours:
        expires_at = datetime.utcnow() + timedelta(hours=body.expires_hours)

    legacy = Legacy(
        user_id=current_user.id,
        content=body.content,
        content_type=body.content_type,
        lat=body.lat,
        lng=body.lng,
        location_name=body.location_name,
        city=body.city,
        country=body.country,
        expires_at=expires_at,
    )
    db.add(legacy)

    profile = _get_or_create_profile(current_user.id, db)
    profile.legacies_dropped += 1
    profile.xp += 20
    db.commit()
    db.refresh(legacy)

    return {"id": legacy.id, "message": "Legacy dropped 📍 Others nearby will find it."}


@router.post("/mint-nft")
async def mint_legacy_nft(
    body: MintNFTBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a legacy as an NFT (actual on-chain minting handled by frontend wallet)."""
    legacy = db.query(Legacy).filter(
        Legacy.id == body.legacy_id,
        Legacy.user_id == current_user.id,
    ).first()
    if not legacy:
        raise HTTPException(status_code=404, detail="Legacy not found")
    if legacy.is_nft:
        raise HTTPException(status_code=400, detail="Already minted as NFT")

    profile = _get_or_create_profile(current_user.id, db)
    if profile.goat_tokens < MINT_NFT_COST:
        raise HTTPException(status_code=400, detail=f"Need {MINT_NFT_COST} GOAT tokens to mint")

    profile.goat_tokens -= MINT_NFT_COST
    legacy.is_nft = True
    legacy.mint_price_tokens = MINT_NFT_COST

    tx = TokenTransaction(
        user_id=current_user.id,
        amount=-MINT_NFT_COST,
        type="nft_mint",
        description=f"Minted Legacy #{legacy.id} as NFT",
        ref_id=legacy.id,
    )
    db.add(tx)
    db.commit()

    return {
        "message":    f"Legacy #{legacy.id} queued for NFT minting 🎨",
        "legacy_id":  legacy.id,
        "tokens_spent": MINT_NFT_COST,
        "remaining_tokens": profile.goat_tokens,
    }


@router.get("/mine")
async def my_legacies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    legacies = (
        db.query(Legacy)
        .filter(Legacy.user_id == current_user.id)
        .order_by(Legacy.created_at.desc())
        .all()
    )
    return [
        {
            "id":            l.id,
            "content":       l.content,
            "content_type":  l.content_type,
            "lat":           l.lat,
            "lng":           l.lng,
            "location_name": l.location_name,
            "city":          l.city,
            "found_count":   l.found_count,
            "is_active":     l.is_active,
            "is_nft":        l.is_nft,
            "created_at":    l.created_at.isoformat(),
            "expires_at":    l.expires_at.isoformat() if l.expires_at else None,
        }
        for l in legacies
    ]
