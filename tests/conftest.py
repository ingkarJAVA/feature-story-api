"""Shared pytest setup: story tests run on a SEPARATE PostgreSQL test database.

The test database is set in TEST_DATABASE_URL (.env). It is wiped and rebuilt
with Alembic migrations, so your real database (DATABASE_URL) is never touched.
This runs BEFORE the app is imported, so the app connects to the test database.
"""
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

_test_url = os.getenv("TEST_DATABASE_URL")
if not _test_url:
    raise RuntimeError(
        "TEST_DATABASE_URL is not set. Add it to .env (see .env.example)."
    )
if _test_url == os.getenv("DATABASE_URL"):
    raise RuntimeError("TEST_DATABASE_URL must differ from DATABASE_URL.")

# Make the whole app use the test database during tests.
os.environ["DATABASE_URL"] = _test_url


@pytest.fixture(scope="session")
def prepared_database():
    """Drop old tables and build a fresh schema with `alembic upgrade head`."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text

    from app.database import engine

    with engine.begin() as conn:
        conn.execute(
            text(
                "DROP TABLE IF EXISTS discovered_clues, session_choices, "
                "game_sessions, clues, suspects, choices, scenes, stories CASCADE"
            )
        )
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.execute(
            text(
                "DROP SEQUENCE IF EXISTS scene_id_seq, choice_id_seq, "
                "game_session_id_seq"
            )
        )

    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    yield
