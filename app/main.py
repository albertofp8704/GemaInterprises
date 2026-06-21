from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import stripe
import os
from datetime import datetime

from .database import get_db, init_db, User, Signal, Script
from .auth import get_current_user, register_user, login_user

# ── App setup ────────────────────────────────────────────────────
app = FastAPI(title="Gema Interprises API", version="1.0.0")

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

class ChatMsg(BaseModel):
    role:    str
    content: str

class ChatIn(BaseModel):
    message: str
    history: list[ChatMsg] = []

class ScriptGenerateIn(BaseModel):
    title:          str
    niche:          str = "general"
    tone:           str = "dramatico"
    target_minutes: int = 5


# ── Startup ──────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    init_db()


# ── Static files ─────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/dayana", StaticFiles(directory="english-teacher", html=True), name="dayana")


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

@app.get("/scripts")
async def scripts_page():
    return FileResponse("static/scripts.html")


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


# ── GEMA AI Chat ─────────────────────────────────────────────────
GEMA_SYSTEM = """Eres GEMA, una asistente de IA holográfica y experta en trading de mercados de predicción de Bitcoin para Kalshi.

Eres parte de Gema Interprises. Tu personalidad: futurista, precisa, ligeramente misteriosa, como un holograma cuántico.

Datos clave de la plataforma:
- Detectamos whale trades ($200+ en tiempo real, mega-whales $1000+ = señal STRONG)
- 83% tasa histórica de aciertos
- Mercados: KXBTC15M (¿BTC +15min?), KXBTCH (¿BTC +1h?), KXBTCD (¿BTC +hoy?)
- Planes: Starter (gratis), Pro ($49/mes, señales live), Enterprise ($199/mes, Telegram + todo)
- Algoritmo: Kelly Criterion — 8% cartera señal STRONG, 5% señal MEDIUM
- Stop-loss: $10 trailing, cooldown 30 min tras pérdida
- Análisis dual: 6-tick corto + 20-tick largo

Reglas:
- Responde SIEMPRE en español
- Máximo 3-4 frases, directo y con confianza
- Usa 1-2 emojis técnicos por respuesta (📡 📈 ⚡ 🔍 etc.)
- No das consejos financieros personalizados
- Si hay dudas sobre el plan, recomienda Pro como punto de entrada"""

@app.post("/api/chat")
async def agent_chat(body: ChatIn):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="Chat service not configured")
    try:
        import anthropic as _a
        client = _a.Anthropic(api_key=api_key)
        msgs = [{"role": m.role, "content": m.content} for m in body.history[-10:]]
        msgs.append({"role": "user", "content": body.message})
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            system=GEMA_SYSTEM,
            messages=msgs,
        )
        return {"response": resp.content[0].text}
    except Exception:
        raise HTTPException(status_code=500, detail="Chat processing error")


# ── GEMA TTS via ElevenLabs (custom cloned voice) ────────────────
class TTSIn(BaseModel):
    text:    str
    voice_id: str = ""

@app.post("/api/tts")
async def agent_tts(body: TTSIn):
    xi_key  = os.getenv("ELEVENLABS_API_KEY")
    voice   = body.voice_id or os.getenv("ELEVENLABS_VOICE_ID", "")
    if not xi_key or not voice:
        raise HTTPException(status_code=503, detail="TTS not configured")
    try:
        import httpx
        async with httpx.AsyncClient() as hc:
            r = await hc.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
                headers={"xi-api-key": xi_key, "Content-Type": "application/json"},
                json={"text": body.text, "model_id": "eleven_multilingual_v2",
                      "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
                timeout=30,
            )
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail="TTS upstream error")
        from fastapi.responses import Response as FResponse
        return FResponse(content=r.content, media_type="audio/mpeg")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="TTS error")


# ── Faceless YouTube script generator ────────────────────────────
SCRIPT_LIMITS    = {"free": 3, "pro": 50, "enterprise": 500}
WORDS_PER_MINUTE = 150

NICHE_LABELS = {
    "general":    "contenido general",
    "historia":   "historia y eventos históricos",
    "true_crime": "true crime / casos reales",
    "finanzas":   "educación financiera",
    "motivacion": "motivación y desarrollo personal",
    "misterio":   "misterio y curiosidades",
    "ciencia":    "ciencia y tecnología",
}

SCRIPT_SYSTEM = """Eres un guionista profesional para canales de YouTube "faceless" (sin presentador visible, solo voz en off sobre B-roll).

Reglas estrictas:
- Escribe SOLO el texto que se va a narrar. Nada de acotaciones de escena, marcas de tiempo, ni etiquetas como "INTRO:" o "[B-ROLL]".
- Las primeras 2 frases deben ser un gancho fuerte que evite que el espectador se vaya.
- Tono solicitado: {tone}. Nicho: {niche_label}.
- Extensión objetivo: ~{words} palabras (~{minutes} min de locución a 150 ppm). Cíñete a ese rango.
- Cierra con una frase que invite a seguir el canal, sin sonar a anuncio forzado.
- Si el tema trata sobre hechos o personas reales, básate en información pública conocida y no presentes afirmaciones inventadas como si fueran noticia verificada. Si dramatizas o especulas, que el tono deje claro que es narrativa, no una nueva afirmación factual."""


def _month_start() -> datetime:
    now = datetime.utcnow()
    return datetime(now.year, now.month, 1)


@app.get("/api/scripts/usage")
async def script_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    used  = db.query(Script).filter(
        Script.user_id == current_user.id,
        Script.created_at >= _month_start(),
    ).count()
    limit = SCRIPT_LIMITS.get(current_user.plan, SCRIPT_LIMITS["free"])
    return {"used": used, "limit": limit, "plan": current_user.plan}


@app.post("/api/scripts/generate")
async def generate_script(
    body: ScriptGenerateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    if len(title) > 200:
        raise HTTPException(status_code=400, detail="title too long (max 200 chars)")

    used  = db.query(Script).filter(
        Script.user_id == current_user.id,
        Script.created_at >= _month_start(),
    ).count()
    limit = SCRIPT_LIMITS.get(current_user.plan, SCRIPT_LIMITS["free"])
    if used >= limit:
        raise HTTPException(
            status_code=402,
            detail=f"Límite mensual de {limit} guiones alcanzado para el plan {current_user.plan}. Mejora tu plan para generar más.",
        )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="Script service not configured")

    minutes     = max(2, min(15, body.target_minutes))
    words       = minutes * WORDS_PER_MINUTE
    niche_label = NICHE_LABELS.get(body.niche, body.niche or "contenido general")

    try:
        import anthropic as _a
        client = _a.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SCRIPT_SYSTEM.format(
                tone=body.tone or "dramático", niche_label=niche_label,
                words=words, minutes=minutes,
            ),
            messages=[{"role": "user", "content": f"Título del vídeo: {title}"}],
        )
        content = resp.content[0].text
    except Exception:
        raise HTTPException(status_code=500, detail="Script generation error")

    script = Script(
        user_id=current_user.id,
        title=title,
        niche=body.niche,
        tone=body.tone,
        content=content,
        word_count=len(content.split()),
    )
    db.add(script)
    db.commit()
    db.refresh(script)

    return {
        "id":         script.id,
        "title":      script.title,
        "content":    script.content,
        "word_count": script.word_count,
        "usage":      {"used": used + 1, "limit": limit, "plan": current_user.plan},
    }


@app.get("/api/scripts")
async def list_scripts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scripts = (
        db.query(Script)
        .filter(Script.user_id == current_user.id)
        .order_by(Script.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id":         s.id,
            "title":      s.title,
            "niche":      s.niche,
            "tone":       s.tone,
            "content":    s.content,
            "word_count": s.word_count,
            "created_at": s.created_at.isoformat(),
        }
        for s in scripts
    ]


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
