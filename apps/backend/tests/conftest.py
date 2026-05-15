import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from auth.hashing import hash_password
from auth.schema import UserModel
from common.database import Base, init_db, reset_engine, set_engine

_TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def engine():
    engine = create_engine(
        _TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine


@pytest.fixture(autouse=True)
def _setup_db(engine):
    set_engine(engine)
    init_db(engine_override=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    reset_engine()


@pytest.fixture
def db_session(engine):
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = test_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    from app import create_app

    app = create_app()

    with TestClient(app) as c:
        yield c


@pytest.fixture
def seed_user(db_session):
    user = UserModel(
        id="test-user-1",
        email="admin@herd.example",
        password_hash=hash_password("admin123"),
        display_name="Admin User",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, seed_user):
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@herd.example", "password": "admin123"},
    )
    token = response.json()["token"]
    return {"Authorization": f"Bearer {token}"}
