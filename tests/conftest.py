import os
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-pytest")
os.environ.setdefault("INTERNAL_API_KEY", "test-internal-key")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_goatarc.db")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app import models_goat  # register GOAT tables

TEST_DB_URL = "sqlite:///./test_goatarc.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    import pathlib
    pathlib.Path("test_goatarc.db").unlink(missing_ok=True)


@pytest.fixture(scope="session")
def client(setup_db):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def auth(client):
    """Register a user and return (token, headers)."""
    r = client.post("/api/auth/register", json={"email": "goat@test.com", "password": "pass1234"})
    assert r.status_code == 200
    token = r.json()["token"]
    return token, {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def auth2(client):
    """Second user for multi-user tests."""
    r = client.post("/api/auth/register", json={"email": "goat2@test.com", "password": "pass1234"})
    assert r.status_code == 200
    token = r.json()["token"]
    return token, {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def headers(auth):
    return auth[1]


@pytest.fixture(scope="session")
def headers2(auth2):
    return auth2[1]
