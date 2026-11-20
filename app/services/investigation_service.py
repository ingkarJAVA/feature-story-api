"""Business logic for the Investigation module, using SQLAlchemy (PostgreSQL).

Every function receives `db` (a SQLAlchemy Session) as its first argument.
The router gets that session from the shared `get_db` dependency.

Errors (the router turns them into HTTP codes):
    KeyError   -> 404 Not Found
    ValueError -> 409 Conflict
"""
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.investigation import Clue, DiscoveredClue, Suspect
from app.models.progress import GameSession
from app.models.story import Scene
from app.schemas.investigation import (
    ClueCreate, ClueUpdate, SuspectCreate, SuspectUpdate
)

MINIMUM_CLUES_FOR_ACCUSATION = 3


# ---------------------------------------------------------------- suspects
def list_suspects(db: Session) -> list[Suspect]:
    return list(db.scalars(select(Suspect).order_by(Suspect.id)).all())


def get_suspect(db: Session, suspect_id: str) -> Suspect:
    suspect = db.get(Suspect, suspect_id)
    if suspect is None:
        raise KeyError(f"Suspect '{suspect_id}' was not found")
    return suspect


def create_suspect(db: Session, payload: SuspectCreate) -> Suspect:
    if db.get(Suspect, payload.id) is not None:
        raise ValueError(f"Suspect '{payload.id}' already exists")
    suspect = Suspect(**payload.model_dump())
    db.add(suspect)
    db.commit()
    db.refresh(suspect)
    return suspect


def update_suspect(db: Session, suspect_id: str, payload: SuspectUpdate) -> Suspect:
    suspect = get_suspect(db, suspect_id)
    for field, value in payload.model_dump(
        exclude_unset=True, exclude_none=True
    ).items():
        setattr(suspect, field, value)
    db.commit()
    db.refresh(suspect)
    return suspect


def delete_suspect(db: Session, suspect_id: str) -> None:
    suspect = get_suspect(db, suspect_id)
    accused = db.scalar(
        select(GameSession.id)
        .where(GameSession.accused_suspect_id == suspect_id)
        .limit(1)
    )
    if accused is not None:
        raise ValueError("Cannot delete a suspect referenced by a game session")
    db.delete(suspect)
    db.commit()


# ------------------------------------------------------------------- clues
def list_clues(
    db: Session, importance: str | None = None, location: str | None = None
) -> list[Clue]:
    query = select(Clue).order_by(Clue.id)
    if importance:
        query = query.where(Clue.importance == importance)
    if location:
        query = query.where(func.lower(Clue.location) == location.casefold())
    return list(db.scalars(query).all())


def get_clue(db: Session, clue_id: str) -> Clue:
    clue = db.get(Clue, clue_id)
    if clue is None:
        raise KeyError(f"Clue '{clue_id}' was not found")
    return clue


def create_clue(db: Session, payload: ClueCreate) -> Clue:
    if db.get(Clue, payload.id) is not None:
        raise ValueError(f"Clue '{payload.id}' already exists")
    if db.get(Scene, payload.related_scene_id) is None:
        raise KeyError(f"Scene '{payload.related_scene_id}' was not found")
    clue = Clue(**payload.model_dump())
    db.add(clue)
    db.commit()
    db.refresh(clue)
    return clue


def update_clue(db: Session, clue_id: str, payload: ClueUpdate) -> Clue:
    clue = get_clue(db, clue_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    scene_id = changes.get("related_scene_id")
    if scene_id and db.get(Scene, scene_id) is None:
        raise KeyError(f"Scene '{scene_id}' was not found")
    for field, value in changes.items():
        setattr(clue, field, value)
    db.commit()
    db.refresh(clue)
    return clue


def delete_clue(db: Session, clue_id: str) -> None:
    clue = get_clue(db, clue_id)
    collected = db.scalar(
        select(DiscoveredClue.session_id)
        .where(DiscoveredClue.clue_id == clue_id)
        .limit(1)
    )
    if collected is not None:
        raise ValueError("Cannot delete a clue already collected by a player")
    db.delete(clue)
    db.commit()


# ----------------------------------------------------------- investigation
def discover_clue(db: Session, session_id: str, clue_id: str) -> Clue:
    session = db.get(GameSession, session_id)
    if session is None:
        raise KeyError(f"Session '{session_id}' was not found")
    clue = db.get(Clue, clue_id)
    if clue is None:
        raise KeyError(f"Clue '{clue_id}' was not found")

    if session.status != "active":
        raise ValueError("The game session is already completed")

    if db.get(DiscoveredClue, (session_id, clue_id)) is not None:
        raise ValueError("This clue has already been discovered")

    if session.current_scene_id != clue.related_scene_id:
        raise ValueError(
            f"This clue can only be discovered in scene '{clue.related_scene_id}'"
        )

    db.add(DiscoveredClue(session_id=session_id, clue_id=clue_id))
    try:
        db.commit()
    except IntegrityError:
        # Two requests tried to save the same clue at the same moment;
        # the composite primary key stopped the second one.
        db.rollback()
        raise ValueError("This clue has already been discovered")
    return clue


def accuse_suspect(db: Session, session_id: str, suspect_id: str) -> dict:
    session = db.get(GameSession, session_id)
    if session is None:
        raise KeyError(f"Session '{session_id}' was not found")
    suspect = db.get(Suspect, suspect_id)
    if suspect is None:
        raise KeyError(f"Suspect '{suspect_id}' was not found")

    if session.status != "active":
        raise ValueError("This game session has already ended")

    clue_count = db.scalar(
        select(func.count())
        .select_from(DiscoveredClue)
        .where(DiscoveredClue.session_id == session_id)
    )
    if clue_count < MINIMUM_CLUES_FOR_ACCUSATION:
        raise ValueError(
            f"At least {MINIMUM_CLUES_FOR_ACCUSATION} unique clues are required; "
            f"you currently have {clue_count}"
        )

    if session.accused_suspect_id is not None:
        raise ValueError("An accusation has already been made")

    correct = bool(suspect.is_guilty)
    session.accused_suspect_id = suspect_id
    # Student 3's get_ending() reads this value to choose the ending.
    session.accusation_correct = correct
    db.commit()

    return {
        "session_id": session_id,
        "suspect_id": suspect_id,
        "correct": correct,
        "message": (
            "Correct accusation! The evidence points to the real killer."
            if correct else
            "Incorrect accusation. The evidence does not support this suspect."
        ),
        "discovered_clue_count": clue_count,
        "status": session.status,
    }
