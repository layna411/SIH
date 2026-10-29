import os
import sys
import pytest

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.config import settings
from app.database.connection import get_db
from app.database.base import Base

# Strictly use dedicated MySQL test schema on XAMPP MySQL server.
# SQLite is strictly prohibited by project specification.
TEST_DATABASE_URL = settings.get_test_database_uri()

test_engine = create_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create schema in isolated MySQL test database, seed baseline roles, and clean up after session."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        from app.services.bootstrap_service import seed_roles
        seed_roles(db)
    finally:
        db.close()
    yield
    # Note: Preserving test database schema and records per mandatory rule:
    # "Never recreate or reset either database to make tests pass. Preserve all existing records."



@pytest.fixture
def db_session():
    """Provide an isolated database session rolled back after every test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
