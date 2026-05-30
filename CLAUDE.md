# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Gema Interprises** is a cryptocurrency trading signals SaaS platform. It delivers real-time trading signals to subscribers with tiered plan access (free / pro / enterprise), Stripe-based subscription management, and a bot-to-backend internal API for injecting signals.

## Running the Project

**Backend (FastAPI):**
```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

**Frontend (landing page preview):**
```bash
npx serve -s . -l 3456
```
The static HTML files are served directly by FastAPI — the `npx serve` command is only for local landing-page development.

**Production start command (Railway):**
```
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

There are no automated tests or linters configured in this repository.

## Required Environment Variables

The app raises `RuntimeError` at startup if these are missing:

| Variable | Purpose |
|---|---|
| `JWT_SECRET` | Signs JWT access tokens |
| `INTERNAL_API_KEY` | Authenticates bot → backend signal delivery |

Optional but needed for full functionality:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | Defaults to SQLite `gema.db` if unset; use `postgresql://` for production |
| `STRIPE_SECRET_KEY` | Stripe payment processing |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook signature verification |

## Architecture

The backend is a single-module FastAPI app split across three files:

- **`app/database.py`** — SQLAlchemy setup, ORM models (`User`, `Signal`), `get_db()` session factory. Automatically converts `postgres://` → `postgresql://` for SQLAlchemy 2.x compatibility.
- **`app/auth.py`** — Password hashing (bcrypt via passlib), JWT creation/decoding (python-jose), and the `get_current_user` dependency used throughout routes.
- **`app/main.py`** — All FastAPI routes, Pydantic request/response models, Stripe webhook handler, and static file mounts.

The frontend is vanilla HTML/CSS/JS with no build step:

- `index.html` — Public landing page (inline styles, ticker animation, pricing).
- `static/login.html`, `static/register.html` — Auth forms that POST to `/api/auth/*`.
- `static/dashboard.html` — Authenticated dashboard; reads JWT from `localStorage` and calls `/api/signals`.

## Key Conventions

**Authentication flow:**
1. Register/login → receive JWT (30-day expiry).
2. Store JWT in `localStorage`; send as `Authorization: Bearer <token>` on every API call.
3. Dashboard and signal endpoints use `Depends(get_current_user)` to enforce authentication.

**Internal bot API:**
Signal injection uses a separate `X-API-Key` header checked against `INTERNAL_API_KEY`. This is distinct from user JWT auth and is used by an external trading bot.

**Database access pattern:**
All route handlers receive a `db: Session = Depends(get_db)` parameter. Always use this dependency — never create sessions directly.

**Plan gating:**
User plan is stored as a string (`"free"`, `"pro"`, `"enterprise"`) on the `User` model. Signal visibility is filtered in API responses based on `current_user.plan`.

**Stripe lifecycle:**
Subscription state is updated via webhook events (`customer.subscription.updated`, `customer.subscription.deleted`). Do not mutate `plan` or `subscription_status` directly from frontend calls — always rely on webhooks for authoritative state.

**Database models:**

`Signal` fields: `market` (e.g. `"BTC/USD"`), `side` (`"YES"/"NO"`), `signal_type` (`"STRONG"/"MEDIUM"`), `whale_amount` (Float), `entry_price`, `result` (`"WIN"/"LOSS"/None`), `pnl`.

`User` fields: `email`, `password_hash`, `plan`, `stripe_customer_id`, `stripe_subscription_id`, `subscription_status`, `telegram_chat_id`, `is_active`.

## Deployment

Deployed on **Railway** via `railway.toml`. Railway injects `DATABASE_URL` (PostgreSQL) and `PORT` automatically. The nixpacks builder detects Python from `runtime.txt` (`python-3.11`). Restart policy is `on_failure`.
