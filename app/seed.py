"""Idempotent seed script: loads the original story data into PostgreSQL.

Run from the project root (after `alembic upgrade head`):
    python -m app.seed

Safe to run many times. Existing rows are never changed or duplicated.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.data import story_data
from app.database import SessionLocal
from app.models.story import Choice, Scene, Story


def _sync_sequence(db: Session, table: str, sequence: str) -> None:
    """Make sure the next generated ID is bigger than every existing ID."""
    max_number = db.execute(
        text(
            f"SELECT COALESCE(MAX(CAST(SUBSTRING(id FROM '[0-9]+$') AS INTEGER)), 0) "
            f"FROM {table}"
        )
    ).scalar_one()
    if max_number > 0:
        db.execute(
            text(f"SELECT setval('{sequence}', GREATEST(:n, (SELECT last_value FROM {sequence})))"),
            {"n": max_number},
        )


def seed(db: Session) -> dict:
    """Insert missing original rows. Returns how many rows were added."""
    added = {"stories": 0, "scenes": 0, "choices": 0}

    story = story_data._INITIAL_STORY
    if db.get(Story, story["id"]) is None:
        db.add(Story(**story))
        added["stories"] += 1
    db.flush()

    for scene in story_data._INITIAL_SCENES:
        if db.get(Scene, scene["id"]) is None:
            db.add(Scene(story_id=story["id"], **scene))
            added["scenes"] += 1
    db.flush()

    for number, (scene_id, text_, next_scene_id) in enumerate(
        story_data._INITIAL_CHOICES, start=1
    ):
        choice_id = f"choice_{number}"
        if db.get(Choice, choice_id) is None:
            db.add(
                Choice(
                    id=choice_id,
                    scene_id=scene_id,
                    choice_text=text_,
                    next_scene_id=next_scene_id,
                )
            )
            added["choices"] += 1
    db.flush()

    _sync_sequence(db, "scenes", "scene_id_seq")
    _sync_sequence(db, "choices", "choice_id_seq")
    db.commit()
    return added


if __name__ == "__main__":
    with SessionLocal() as session:
        result = seed(session)
    print(f"Seed finished. Added: {result}")
