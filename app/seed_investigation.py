"""Idempotent seed script: loads the original suspects and clues into PostgreSQL.

Run from the project root, AFTER `alembic upgrade head` and `python -m app.seed`
(the clues point to scenes, so the scenes must already exist):

    python -m app.seed_investigation

Safe to run many times. Existing rows are never changed or duplicated.
"""
from sqlalchemy.orm import Session

from app.data import investigation_data
from app.database import SessionLocal
from app.models.investigation import Clue, Suspect
from app.models.story import Scene


def seed(db: Session) -> dict:
    """Insert missing suspects and clues. Returns how many rows were added."""
    added = {"suspects": 0, "clues": 0}

    for suspect in investigation_data.suspects.values():
        if db.get(Suspect, suspect["id"]) is None:
            db.add(Suspect(**suspect))
            added["suspects"] += 1
    db.flush()

    for clue in investigation_data.clues.values():
        if db.get(Scene, clue["related_scene_id"]) is None:
            raise RuntimeError(
                f"Scene '{clue['related_scene_id']}' is missing. "
                "Run `python -m app.seed` first."
            )
        if db.get(Clue, clue["id"]) is None:
            db.add(Clue(**clue))
            added["clues"] += 1
    db.commit()
    return added


if __name__ == "__main__":
    with SessionLocal() as session:
        result = seed(session)
    print(f"Investigation seed finished. Added: {result}")
