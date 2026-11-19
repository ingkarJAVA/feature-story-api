"""Shared database setup. ALL students import from this one file.

- Base:         the single SQLAlchemy declarative base for every model
- engine:       the single connection pool
- SessionLocal: creates database sessions
- get_db:       FastAPI dependency that gives each request its own session
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Read variables from the .env file in the project root (if it exists).
# Variables already set in the environment (for example by pytest) win.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and fill in "
        "your PostgreSQL password."
    )


class Base(DeclarativeBase):
    """The one shared base class for all SQLAlchemy models."""


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    """FastAPI dependency: one session per request, always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
