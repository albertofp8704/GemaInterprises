"""
Wallet integration — MetaMask / WalletConnect.

Flow:
  1. GET  /api/wallet/challenge        → server issues a sign-message challenge
  2. POST /api/wallet/connect          → client sends address + signed challenge
  3. Server verifies signature → links wallet_address to the user account
  4. POST /api/wallet/mint-tokens      → bridge in-app GOAT tokens to on-chain ERC-20
  5. POST /api/wallet/mint-legacy-nft  → mint a Legacy as ERC-721 NFT
  6. POST /api/wallet/mint-flashcard   → mint a FlashCard as ERC-1155 NFT
"""
import os
import secrets
import time
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from eth_account import Account
from eth_account.messages import encode_defunct

from ..database import get_db, User
from ..auth import get_current_user
from ..models_goat import PlayerProfile, Legacy, UserFlashCard, FlashCard, TokenTransaction
from .profile import _get_or_create_profile

router = APIRouter(prefix="/api/wallet", tags=["wallet"])

# In production store challenges in Redis with TTL; here use a simple in-memory dict
_challenges: dict[int, tuple[str, float]] = {}  # user_id → (nonce, expires_at)
CHALLENGE_TTL = 300  # 5 minutes

GOAT_TOKEN_ADDRESS    = os.getenv("GOAT_TOKEN_ADDRESS", "")
LEGACY_NFT_ADDRESS    = os.getenv("LEGACY_NFT_ADDRESS", "")
FLASHCARD_NFT_ADDRESS = os.getenv("FLASHCARD_NFT_ADDRESS", "")
BACKEND_WALLET_KEY    = os.getenv("BACKEND_WALLET_KEY", "")  # backend signer private key
RPC_URL               = os.getenv("WEB3_RPC_URL", "https://polygon-rpc.com")

BRIDGE_COST_TOKENS  = 50   # GOAT tokens fee to bridge in-app → on-chain


class ConnectWalletBody(BaseModel):
    wallet_address: str
    signature: str


class MintTokensBody(BaseModel):
    amount_tokens: int   # in-app tokens to bridge on-chain (min 100)


class MintLegacyBody(BaseModel):
    legacy_id: int
    token_uri: str   # IPFS URI with the legacy metadata JSON


class MintFlashCardBody(BaseModel):
    user_flashcard_id: int


@router.get("/challenge")
async def get_challenge(current_user: User = Depends(get_current_user)):
    """Returns a unique message the user must sign with MetaMask."""
    nonce = secrets.token_hex(16)
    _challenges[current_user.id] = (nonce, time.time() + CHALLENGE_TTL)
    message = (
        f"GOAT Arc Authentication\n"
        f"User: {current_user.email}\n"
        f"Nonce: {nonce}\n"
        f"Timestamp: {int(time.time())}"
    )
    return {"message": message, "nonce": nonce}


@router.post("/connect")
async def connect_wallet(
    body: ConnectWalletBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Verify MetaMask signature and link wallet address to user account."""
    challenge = _challenges.get(current_user.id)
    if not challenge:
        raise HTTPException(status_code=400, detail="Request a challenge first")
    nonce, expires_at = challenge
    if time.time() > expires_at:
        del _challenges[current_user.id]
        raise HTTPException(status_code=400, detail="Challenge expired, request a new one")

    # Reconstruct the message that was signed
    message_text = (
        f"GOAT Arc Authentication\n"
        f"User: {current_user.email}\n"
        f"Nonce: {nonce}\n"
    )

    try:
        msg        = encode_defunct(text=message_text)
        recovered  = Account.recover_message(msg, signature=body.signature)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if recovered.lower() != body.wallet_address.lower():
        raise HTTPException(status_code=401, detail="Signature does not match wallet address")

    # Save wallet address to user
    current_user.wallet_address = body.wallet_address.lower()
    del _challenges[current_user.id]
    db.commit()

    # Bonus tokens for connecting wallet
    profile = _get_or_create_profile(current_user.id, db)
    profile.goat_tokens += 50
    tx = TokenTransaction(
        user_id=current_user.id, amount=50, type="wallet_connect",
        description=f"Wallet conectada: {body.wallet_address[:10]}..."
    )
    db.add(tx)
    db.commit()

    return {
        "message":        "Wallet conectada! 🦊 +50 GOAT tokens",
        "wallet_address": body.wallet_address.lower(),
        "bonus_tokens":   50,
    }


@router.get("/status")
async def wallet_status(
    current_user: User = Depends(get_current_user),
):
    address = getattr(current_user, "wallet_address", None)
    return {
        "connected":       bool(address),
        "wallet_address":  address,
        "contracts": {
            "goat_token":    GOAT_TOKEN_ADDRESS,
            "legacy_nft":    LEGACY_NFT_ADDRESS,
            "flashcard_nft": FLASHCARD_NFT_ADDRESS,
            "network":       "Polygon",
            "chain_id":      137,
        },
    }


@router.post("/mint-tokens")
async def mint_tokens_onchain(
    body: MintTokensBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bridge in-app GOAT tokens → on-chain ERC-20 (requires connected wallet)."""
    address = getattr(current_user, "wallet_address", None)
    if not address:
        raise HTTPException(status_code=400, detail="Connect your wallet first")

    if body.amount_tokens < 100:
        raise HTTPException(status_code=400, detail="Minimum bridge amount: 100 tokens")

    total_cost = body.amount_tokens + BRIDGE_COST_TOKENS
    profile    = _get_or_create_profile(current_user.id, db)

    if profile.goat_tokens < total_cost:
        raise HTTPException(status_code=400, detail=f"Need {total_cost} tokens ({body.amount_tokens} + {BRIDGE_COST_TOKENS} fee)")

    profile.goat_tokens -= total_cost
    tx = TokenTransaction(
        user_id=current_user.id, amount=-total_cost, type="bridge_to_chain",
        description=f"Bridge {body.amount_tokens} GOAT → on-chain"
    )
    db.add(tx)
    db.commit()

    # In production: call GOATToken.mintTo() via web3.py here
    # wei_amount = body.amount_tokens * 10**18
    # contract.functions.mintTo(address, wei_amount, "bridge").transact(...)
    amount_onchain = body.amount_tokens * (10 ** 18)  # convert to wei

    return {
        "message":         f"{body.amount_tokens} GOAT tokens bridged to {address[:10]}... 🔗",
        "amount_wei":      str(amount_onchain),
        "wallet_address":  address,
        "contract":        GOAT_TOKEN_ADDRESS,
        "status":          "pending_onchain",
        "note":            "Deploy contract and set GOAT_TOKEN_ADDRESS to activate on-chain minting",
    }


@router.post("/mint-legacy-nft")
async def mint_legacy_nft_onchain(
    body: MintLegacyBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mint a Legacy as an ERC-721 NFT on Polygon."""
    address = getattr(current_user, "wallet_address", None)
    if not address:
        raise HTTPException(status_code=400, detail="Connect your wallet first")

    legacy = db.query(Legacy).filter(
        Legacy.id == body.legacy_id,
        Legacy.user_id == current_user.id,
    ).first()
    if not legacy:
        raise HTTPException(status_code=404, detail="Legacy not found")
    if legacy.is_nft and legacy.nft_token_id:
        raise HTTPException(status_code=400, detail="Already minted as NFT")

    profile = _get_or_create_profile(current_user.id, db)
    if profile.goat_tokens < 200:
        raise HTTPException(status_code=400, detail="Need 200 GOAT tokens to mint Legacy NFT")

    profile.goat_tokens -= 200
    legacy.is_nft = True
    # nft_token_id set after on-chain tx confirms

    tx = TokenTransaction(
        user_id=current_user.id, amount=-200, type="nft_mint",
        description=f"Legacy #{legacy.id} NFT mint",
        ref_id=legacy.id,
    )
    db.add(tx)
    db.commit()

    return {
        "message":        f"Legacy #{legacy.id} queued for NFT mint on Polygon 🎨",
        "token_uri":      body.token_uri,
        "wallet_address": address,
        "contract":       LEGACY_NFT_ADDRESS,
        "legacy_id":      legacy.id,
        "status":         "pending_onchain",
    }


@router.post("/mint-flashcard")
async def mint_flashcard_onchain(
    body: MintFlashCardBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mint a Flash Card as an ERC-1155 NFT on Polygon."""
    address = getattr(current_user, "wallet_address", None)
    if not address:
        raise HTTPException(status_code=400, detail="Connect your wallet first")

    uc = db.query(UserFlashCard).filter(
        UserFlashCard.id == body.user_flashcard_id,
        UserFlashCard.user_id == current_user.id,
    ).first()
    if not uc:
        raise HTTPException(status_code=404, detail="Flash card not found in your collection")
    if uc.is_nft:
        raise HTTPException(status_code=400, detail="Already an NFT")

    card    = db.query(FlashCard).filter(FlashCard.id == uc.card_id).first()
    profile = _get_or_create_profile(current_user.id, db)

    mint_cost = 100
    if profile.goat_tokens < mint_cost:
        raise HTTPException(status_code=400, detail=f"Need {mint_cost} GOAT tokens to mint card NFT")

    profile.goat_tokens -= mint_cost
    uc.is_nft = True

    tx = TokenTransaction(
        user_id=current_user.id, amount=-mint_cost, type="nft_mint",
        description=f"FlashCard NFT: {card.name if card else uc.card_id}",
        ref_id=uc.card_id,
    )
    db.add(tx)
    db.commit()

    return {
        "message":        f"'{card.name if card else 'Card'}' minted as NFT on Polygon 🃏",
        "card_id":        uc.card_id,
        "wallet_address": address,
        "contract":       FLASHCARD_NFT_ADDRESS,
        "status":         "pending_onchain",
    }
