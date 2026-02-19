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


def init_db() -> None:
    """Create all database tables. Called at application startup."""
    Base.metadata.create_all(bind=engine)
