"""
SecureDocAI — Database Layer
==============================
SQLAlchemy engine, session management, and base model.
Uses SQLite for POC, easily swappable to PostgreSQL for production.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from typing import Generator

from config.settings import get_settings


# ── Base Model ──

class Base(DeclarativeBase):
    """SQLAlchemy declarative base for all ORM models."""
    pass


# ── Engine & Session Factory ──

settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=settings.app_debug,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ── Dependency ──

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    Ensures the session is closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


import time
import structlog
from sqlalchemy.exc import OperationalError

logger = structlog.get_logger(__name__)

def init_db() -> None:
    """Create all database tables. Called at application startup. 
    Includes connection retries to ensure resilience against DB startup delays."""
    max_retries = 5
    retry_interval = 3  # seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("database_initialized", attempt=attempt)
            break
        except OperationalError as e:
            if attempt == max_retries:
                logger.error("database_initialization_failed", error=str(e), attempts=attempt)
                raise e
            logger.warning("database_connection_failed", attempt=attempt, retry_in=retry_interval, error=str(e))
            time.sleep(retry_interval)
