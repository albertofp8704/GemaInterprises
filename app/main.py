from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import stripe
import os
from datetime import datetime

from .database import get_db, init_db, User, Signal
from .auth import get_current_user, register_user, login_user
from . import models_goat  # registers GOAT Arc tables on Base.metadata
from .routes.profile     import router as profile_router
from .routes.quests      import router as quests_router
from .routes.predictions import router as predictions_router
from .routes.villain     import router as villain_router
from .routes.campaigns   import router as campaigns_router
from .routes.legacy      import router as legacy_router
from .routes.tokens      import router as tokens_router
from .routes.wallet      import router as wallet_router

# ── App setup ────────────────────────────────────────────────────
app = FastAPI(title="Gema Interprises API", version="1.0.0")

for _router in (
    profile_router, quests_router, predictions_router,
    villain_router, campaigns_router, legacy_router, tokens_router,
    wallet_router,
):
    app.include_router(_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stripe.api_key            = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET     = os.getenv("STRIPE_WEBHOOK_SECRET", "")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
if not INTERNAL_API_KEY:
    raise RuntimeError("INTERNAL_API_KEY env var is required — set it in Railway")

PLANS = {
    "pro":        {"name": "Gema Pro",        "amount": 4900},
    "enterprise": {"name": "Gema Enterprise", "amount": 19900},
}


# ── Pydantic models ──────────────────────────────────────────────
class AuthRequest(BaseModel):
    email:    str
    password: str

class SignalIn(BaseModel):
    market:       str
    side:         str
    signal_type:  str
    whale_amount: float
    entry_price:  float

class SettleIn(BaseModel):
    result: str       # WIN | LOSS
    pnl:    float


# ── Startup ──────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    init_db()
    from .seed_goat import seed
    seed()


# ── Health check (Railway uses this to verify the app is alive) ──
@app.get("/health")
async def health():
    return {"status": "ok", "app": "GOAT Arc"}


# ── Static files ─────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Pages ────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return FileResponse("index.html")

@app.get("/login")
async def login_page():
    return FileResponse("static/login.html")

@app.get("/register")
async def register_page():
    return FileResponse("static/register.html")

@app.get("/dashboard")
async def dashboard_page():
    return FileResponse("static/dashboard.html")


# ── Auth ─────────────────────────────────────────────────────────
@app.post("/api/auth/register")
async def register(body: AuthRequest, db: Session = Depends(get_db)):
    return await register_user(body.email, body.password, db)

@app.post("/api/auth/login")
async def login(body: AuthRequest, db: Session = Depends(get_db)):
    return await login_user(body.email, body.password, db)

@app.get("/api/auth/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id":                  current_user.id,
        "email":               current_user.email,
        "plan":                current_user.plan,
        "subscription_status": current_user.subscription_status,
        "created_at":          current_user.created_at.isoformat(),
    }


# ── Stripe ───────────────────────────────────────────────────────
@app.post("/api/stripe/create-checkout/{plan}")
async def create_checkout(
    plan: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if plan not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")

    plan_data = PLANS[plan]
    base_url  = str(request.base_url).rstrip("/")

    # Create Stripe customer if needed
    if not current_user.stripe_customer_id:
        customer = stripe.Customer.create(email=current_user.email)
        current_user.stripe_customer_id = customer.id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=current_user.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency":     "usd",
                "product_data": {"name": plan_data["name"]},
                "unit_amount":  plan_data["amount"],
                "recurring":    {"interval": "month"},
            },
            "quantity": 1,
        }],
        mode="subscription",
        success_url=f"{base_url}/dashboard?success=1&plan={plan}&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{base_url}/dashboard?canceled=1",
        metadata={"user_id": str(current_user.id), "plan": plan},
    )
    return {"url": session.url}


@app.post("/api/stripe/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    etype = event["type"]

    if etype == "checkout.session.completed":
        s       = event["data"]["object"]
        user_id = int(s["metadata"]["user_id"])
        plan    = s["metadata"]["plan"]
        user    = db.query(User).filter(User.id == user_id).first()
        if user:
            user.plan                   = plan
            user.subscription_status    = "active"
            user.stripe_subscription_id = s.get("subscription")
            db.commit()

    elif etype == "customer.subscription.deleted":
        sub  = event["data"]["object"]
        user = db.query(User).filter(User.stripe_subscription_id == sub["id"]).first()
        if user:
            user.plan                = "free"
            user.subscription_status = "inactive"
            db.commit()

    elif etype == "invoice.payment_failed":
        sub_id = event["data"]["object"].get("subscription")
        if sub_id:
            user = db.query(User).filter(User.stripe_subscription_id == sub_id).first()
            if user:
                user.subscription_status = "past_due"
                db.commit()

    return {"status": "ok"}


# ── Signals (internal — called by GemaBot) ───────────────────────
@app.post("/api/signals")
async def create_signal(
    signal: SignalIn,
    request: Request,
    db: Session = Depends(get_db),
):
    if request.headers.get("X-API-Key") != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    s = Signal(**signal.dict())
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id, "status": "created"}


@app.patch("/api/signals/{signal_id}/settle")
async def settle_signal(
    signal_id: int,
    body: SettleIn,
    request: Request,
    db: Session = Depends(get_db),
):
    if request.headers.get("X-API-Key") != INTERNAL_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    s = db.query(Signal).filter(Signal.id == signal_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Signal not found")

    s.result     = body.result
    s.pnl        = body.pnl
    s.settled_at = datetime.utcnow()
    db.commit()
    return {"status": "settled"}


# ── Verify Stripe session & activate plan ────────────────────────
@app.post("/api/stripe/verify-session")
async def verify_session(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    body       = await request.json()
    session_id = body.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if session.payment_status == "paid" and str(session.metadata.get("user_id")) == str(current_user.id):
        plan = session.metadata.get("plan", "pro")
        current_user.plan                   = plan
        current_user.subscription_status    = "active"
        current_user.stripe_subscription_id = session.subscription
        db.commit()
        return {"plan": plan, "status": "activated"}

    raise HTTPException(status_code=400, detail="Payment not confirmed")


# ── Signals (frontend — read only) ───────────────────────────────
@app.get("/api/signals")
async def get_signals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    signals = db.query(Signal).order_by(Signal.timestamp.desc()).limit(50).all()
    return [
        {
            "id":           s.id,
            "market":       s.market,
            "side":         s.side,
            "signal_type":  s.signal_type,
            "whale_amount": s.whale_amount,
            "entry_price":  s.entry_price,
            "timestamp":    s.timestamp.isoformat(),
            "result":       s.result,
            "pnl":          s.pnl,
        }
        for s in signals
    ]


@app.get("/api/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settled = db.query(Signal).filter(Signal.result.isnot(None)).all()
    wins    = [s for s in settled if s.result == "WIN"]
    total_pnl = sum(s.pnl or 0 for s in settled)
    pending   = db.query(Signal).filter(Signal.result.is_(None)).count()

    return {
        "total_signals": len(settled),
        "wins":          len(wins),
        "losses":        len(settled) - len(wins),
        "winrate":       round(len(wins) / len(settled) * 100, 1) if settled else 0,
        "total_pnl":     round(total_pnl, 2),
        "pending":       pending,
    }
