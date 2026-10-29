import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.database.base import Base

logger = logging.getLogger("eduresolve.database")

# Build connection URL safely via SQLAlchemy URL utilities
database_url = settings.get_database_uri()
safe_url = settings.get_safe_database_uri()

# Create the single SQLAlchemy 2.x Engine with connection pooling and pre-ping
engine = create_engine(
    database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
)

# Reusable session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session
    and guarantees it is closed upon completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection() -> bool:
    """
    Execute a real SELECT 1 against the configured XAMPP MySQL database.
    Returns True if connection succeeds, False otherwise.
    Never exposes passwords or sensitive credentials in logs.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection verification failed for {safe_url}: {e}")
        return False

