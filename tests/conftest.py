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
                "DROP TABLE IF EXISTS users, discovered_clues, session_choices, "
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

@pytest.fixture
def fresh_game_data(prepared_database):
    """Reset and seed the PostgreSQL test database."""

    from sqlalchemy import text
    from app.database import SessionLocal
    from app.seed import seed as seed_story
    from app.seed_investigation import seed as seed_investigation

    with SessionLocal() as db:
        db.execute(text(
            "TRUNCATE users, discovered_clues, session_choices, "
            "game_sessions, clues, suspects, choices, scenes, "
            "stories RESTART IDENTITY CASCADE"
        ))

        db.execute(text("ALTER SEQUENCE scene_id_seq RESTART WITH 1"))
        db.execute(text("ALTER SEQUENCE choice_id_seq RESTART WITH 1"))
        db.execute(text("ALTER SEQUENCE game_session_id_seq RESTART WITH 1"))

        db.commit()

        seed_story(db)
        seed_investigation(db)


@pytest.fixture
def make_test_user(prepared_database):
    """Create a test user and return their authentication headers."""

    from app.database import SessionLocal
    from app.models.user import User
    from app.core.security import hash_password, create_access_token

    def create_user(username: str, role: str = "user"):
        with SessionLocal() as db:
            user = User(
                email=f"{username}@example.com",
                username=username,
                hashed_password=hash_password("TestPassword123"),
                role=role,
                is_active=True,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

            return {
                "id": user.id,
                "headers": {
                    "Authorization": (
                        f"Bearer {create_access_token(user.id)}"
                    )
                },
            }

    return create_user


@pytest.fixture
def player_user(fresh_game_data, make_test_user):
    return make_test_user("shrek")


@pytest.fixture
def admin_user(fresh_game_data, make_test_user):
    return make_test_user("admin", role="admin")