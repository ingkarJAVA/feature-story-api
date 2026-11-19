
"""Business logic for Player Progress & Endings."""

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.story import Scene, Choice
from app.models.progress import GameSession, SessionChoice


ENDINGS = {
    "true_detective": {
        "ending_id": "true_detective",
        "title": "The True Detective",
        "description": (
            "Shrek collected the evidence and correctly identified "
            "the murderer. The truth about King Harold's death is revealed."
        ),
    },
    "wrong_suspect": {
        "ending_id": "wrong_suspect",
        "title": "The Wrong Accusation",
        "description": (
            "Shrek accused the wrong person. The real murderer "
            "remains free, and justice has not been served."
        ),
    },
    "new_king": {
        "ending_id": "new_king",
        "title": "A New King",
        "description": (
            "The investigation ends without a correct accusation. "
            "The kingdom moves forward under a new ruler."
        ),
    },
    "secret_ending": {
        "ending_id": "secret_ending",
        "title": "The Hidden Truth",
        "description": (
            "Shrek discovered the secret evidence and uncovered "
            "a hidden truth behind the king's death."
        ),
    },
}


def get_discovered_clue_ids(db: Session, session_id: str) -> list[str]:
    """Read discovered clues from Student 2's database table."""

    rows = db.execute(
        text(
            "SELECT clue_id FROM discovered_clues "
            "WHERE session_id = :session_id"
        ),
        {"session_id": session_id},
    ).scalars().all()

    return list(rows)


def session_to_dict(db: Session, session: GameSession) -> dict:
    """Convert database records into the existing API response format."""

    choices = db.scalars(
        select(SessionChoice.choice_id)
        .where(SessionChoice.session_id == session.id)
        .order_by(SessionChoice.id)
    ).all()

    return {
        "id": session.id,
        "player_name": session.player_name,
        "current_scene_id": session.current_scene_id,
        "discovered_clue_ids": get_discovered_clue_ids(db, session.id),
        "accused_suspect_id": session.accused_suspect_id,
        "status": session.status,
        "ending_id": session.ending_id,
        "choices_history": list(choices),
    }


def create_session(db: Session, player_name: str) -> dict:
    """Create a new game session in PostgreSQL."""

    initial_scene = db.get(Scene, "scene_1")

    if initial_scene is None:
        raise KeyError("Initial scene not found")

    session_number = db.execute(
        text("SELECT nextval('game_session_id_seq')")
    ).scalar_one()

    session = GameSession(
        id=f"session_{session_number}",
        player_name=player_name,
        current_scene_id=initial_scene.id,
        status="active",
        ending_id=None,
        accused_suspect_id=None,
        accusation_correct=None,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session_to_dict(db, session)


def get_session(db: Session, session_id: str) -> dict:
    """Retrieve a game session from PostgreSQL."""

    session = db.get(GameSession, session_id)

    if session is None:
        raise KeyError("Session not found")

    return session_to_dict(db, session)


def update_session(
    db: Session,
    session_id: str,
    player_name: str,
) -> dict:
    """Update the player's name."""

    session = db.get(GameSession, session_id)

    if session is None:
        raise KeyError("Session not found")

    if session.status != "active":
        raise ValueError("Cannot update a completed session")

    session.player_name = player_name

    db.commit()
    db.refresh(session)

    return session_to_dict(db, session)


def delete_session(db: Session, session_id: str) -> None:
    """Delete a game session and its choice history."""

    session = db.get(GameSession, session_id)

    if session is None:
        raise KeyError("Session not found")

    db.delete(session)
    db.commit()


def make_choice(
    db: Session,
    session_id: str,
    choice_id: str,
) -> dict:
    """Record a choice and move the player to the next scene."""

    session = db.get(GameSession, session_id)

    if session is None:
        raise KeyError("Session not found")

    if session.status != "active":
        raise ValueError("This session is already completed")

    current_scene = db.get(Scene, session.current_scene_id)

    if current_scene is None:
        raise KeyError("Current scene not found")

    if current_scene.is_ending:
        raise ValueError(
            "The player has already reached the final scene"
        )

    choice = db.get(Choice, choice_id)

    if choice is None:
        raise KeyError("Choice not found")

    if choice.scene_id != session.current_scene_id:
        raise ValueError(
            "This choice does not belong to the current scene"
        )

    next_scene = db.get(Scene, choice.next_scene_id)

    if next_scene is None:
        raise ValueError("The destination scene does not exist")

    history_record = SessionChoice(
        session_id=session.id,
        choice_id=choice.id,
    )

    db.add(history_record)
    session.current_scene_id = next_scene.id

    db.commit()
    db.refresh(session)

    return session_to_dict(db, session)


def determine_ending(
    db: Session,
    session: GameSession,
) -> str:
    """Determine the ending using stored investigation results."""

    discovered_clues = set(
        get_discovered_clue_ids(db, session.id)
    )

    secret_clues = {
        "secret_passage",
        "golden_fabric",
        "charming_letter",
    }

    if secret_clues.issubset(discovered_clues):
        return "secret_ending"

    if session.accusation_correct is True:
        return "true_detective"

    if session.accusation_correct is False:
        return "wrong_suspect"

    return "new_king"


def get_ending(db: Session, session_id: str) -> dict:
    """Determine and save the player's final ending."""

    session = db.get(GameSession, session_id)

    if session is None:
        raise KeyError("Session not found")

    if session.status == "completed":
        return ENDINGS[session.ending_id]

    current_scene = db.get(Scene, session.current_scene_id)

    if current_scene is None:
        raise KeyError("Current scene not found")

    if not current_scene.is_ending:
        raise ValueError(
            "The story has not reached its final scene"
        )

    ending_id = determine_ending(db, session)

    session.ending_id = ending_id
    session.status = "completed"

    db.commit()

    return ENDINGS[ending_id]
