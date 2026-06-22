import sys
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_db
from app.main import app
from app.auth.utils import hash_password, create_access_token
from app.auth.models import User


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, follow_redirects=False) as c:
        yield c
    app.dependency_overrides.clear()


def _create_user(db, username="testuser", email="test@test.com",
                  password="test123", role="professional"):
    user = User(
        username=username,
        email=email,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_user(db_session):
    return _create_user(db_session)


@pytest.fixture
def test_admin(db_session):
    return _create_user(db_session, username="admin", email="admin@test.com",
                        password="admin123", role="admin")


@pytest.fixture
def test_viewer(db_session):
    return _create_user(db_session, username="viewer", email="viewer@test.com",
                        password="viewer123", role="viewer")


def auth_headers(user):
    token = create_access_token({"sub": user.username, "role": user.role})
    return {"Authorization": f"Bearer {token}"}
