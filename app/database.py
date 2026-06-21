from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gema.db")
# Railway uses postgres:// but SQLAlchemy requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id                     = Column(Integer, primary_key=True, index=True)
    email                  = Column(String, unique=True, index=True, nullable=False)
    password_hash          = Column(String, nullable=False)
    plan                   = Column(String, default="free")        # free | pro | enterprise
    stripe_customer_id     = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)
    subscription_status    = Column(String, default="inactive")    # active | inactive | canceled
    telegram_chat_id       = Column(String, nullable=True)
    created_at             = Column(DateTime, default=datetime.utcnow)
    is_active              = Column(Boolean, default=True)


class Signal(Base):
    __tablename__ = "signals"
    id           = Column(Integer, primary_key=True, index=True)
    market       = Column(String, nullable=False)
    side         = Column(String, nullable=False)       # YES | NO
    signal_type  = Column(String, nullable=False)       # STRONG | MEDIUM
    whale_amount = Column(Float, nullable=False)
    entry_price  = Column(Float, nullable=False)
    timestamp    = Column(DateTime, default=datetime.utcnow)
    result       = Column(String, nullable=True)        # WIN | LOSS | PENDING
    pnl          = Column(Float, nullable=True)
    settled_at   = Column(DateTime, nullable=True)


class Script(Base):
    __tablename__ = "scripts"
    id                 = Column(Integer, primary_key=True, index=True)
    user_id            = Column(Integer, nullable=False, index=True)
    title              = Column(String, nullable=False)
    niche              = Column(String, default="general")
    tone               = Column(String, default="dramatico")
    content            = Column(Text, nullable=False)
    word_count         = Column(Integer, default=0)
    video_status       = Column(String, default="none")  # none | generating | done | failed
    video_url          = Column(String, nullable=True)
    subtitles_url      = Column(String, nullable=True)
    video_requested_at = Column(DateTime, nullable=True, index=True)
    created_at         = Column(DateTime, default=datetime.utcnow, index=True)


class Scene(Base):
    __tablename__ = "scenes"
    id           = Column(Integer, primary_key=True, index=True)
    script_id    = Column(Integer, nullable=False, index=True)
    order        = Column(Integer, nullable=False)
    text         = Column(Text, nullable=False)
    image_prompt = Column(Text, nullable=True)
    image_url    = Column(String, nullable=True)
    status       = Column(String, default="pending")  # pending | queued | generating | done | failed
    created_at   = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
