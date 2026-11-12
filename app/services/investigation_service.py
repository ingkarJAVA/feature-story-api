from app.data.investigation_data import clues, suspects
from app.schemas.investigation import (
    ClueCreate, ClueUpdate, SuspectCreate, SuspectUpdate
)

MINIMUM_CLUES_FOR_ACCUSATION = 3


def _sessions():
    """
    Shared integration contract:
    Student 3 must expose `sessions` from app.data.progress_data as a dict:
    {session_id: {
        "id": str, "current_scene_id": str,
        "discovered_clue_ids": list[str],
        "accused_suspect_id": str | None,
        "status": "active" | "completed",
        "ending_id": str | None
    }}
    """
    try:
        from app.data.progress_data import sessions
    except ImportError as exc:
        raise RuntimeError(
            "Integration required: Student 3 must create "
            "app.data.progress_data.sessions"
        ) from exc
    return sessions


def _scene_exists(scene_id: str) -> bool:
    try:
        from app.data.story_data import scenes
        return scene_id in scenes
    except (ImportError, AttributeError):
        # During isolated development, scene validation can be integrated later.
        return True


def list_suspects():
    return list(suspects.values())


def get_suspect(suspect_id: str):
    if suspect_id not in suspects:
        raise KeyError(f"Suspect '{suspect_id}' was not found")
    return suspects[suspect_id]


def create_suspect(payload: SuspectCreate):
    if payload.id in suspects:
        raise ValueError(f"Suspect '{payload.id}' already exists")
    suspects[payload.id] = payload.model_dump()
    return suspects[payload.id]


def update_suspect(suspect_id: str, payload: SuspectUpdate):
    if suspect_id not in suspects:
        raise KeyError(f"Suspect '{suspect_id}' was not found")
    suspects[suspect_id].update(payload.model_dump(exclude_unset=True, exclude_none=True))
    return suspects[suspect_id]


def delete_suspect(suspect_id: str):
    if suspect_id not in suspects:
        raise KeyError(f"Suspect '{suspect_id}' was not found")
    if any(s.get("accused_suspect_id") == suspect_id for s in _sessions().values()):
        raise ValueError("Cannot delete a suspect referenced by a game session")
    del suspects[suspect_id]


def list_clues(importance: str | None = None, location: str | None = None):
    result = list(clues.values())
    if importance:
        result = [c for c in result if c["importance"] == importance]
    if location:
        result = [c for c in result if c["location"].casefold() == location.casefold()]
    return result


def get_clue(clue_id: str):
    if clue_id not in clues:
        raise KeyError(f"Clue '{clue_id}' was not found")
    return clues[clue_id]


def create_clue(payload: ClueCreate):
    if payload.id in clues:
        raise ValueError(f"Clue '{payload.id}' already exists")
    if not _scene_exists(payload.related_scene_id):
        raise KeyError(f"Scene '{payload.related_scene_id}' was not found")
    clues[payload.id] = payload.model_dump()
    return clues[payload.id]


def update_clue(clue_id: str, payload: ClueUpdate):
    if clue_id not in clues:
        raise KeyError(f"Clue '{clue_id}' was not found")
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    scene_id = changes.get("related_scene_id")
    if scene_id and not _scene_exists(scene_id):
        raise KeyError(f"Scene '{scene_id}' was not found")
    clues[clue_id].update(changes)
    return clues[clue_id]


def delete_clue(clue_id: str):
    if clue_id not in clues:
        raise KeyError(f"Clue '{clue_id}' was not found")
    if any(clue_id in s.get("discovered_clue_ids", []) for s in _sessions().values()):
        raise ValueError("Cannot delete a clue already collected by a player")
    del clues[clue_id]


def discover_clue(session_id: str, clue_id: str):
    sessions = _sessions()
    if session_id not in sessions:
        raise KeyError(f"Session '{session_id}' was not found")
    if clue_id not in clues:
        raise KeyError(f"Clue '{clue_id}' was not found")

    session = sessions[session_id]
    if session.get("status") != "active":
        raise ValueError("The game session is already completed")

    collected = session.setdefault("discovered_clue_ids", [])
    if clue_id in collected:
        raise ValueError("This clue has already been discovered")

    clue = clues[clue_id]
    if session.get("current_scene_id") != clue["related_scene_id"]:
        raise ValueError(
            f"This clue can only be discovered in scene '{clue['related_scene_id']}'"
        )

    collected.append(clue_id)
    return clue


def accuse_suspect(session_id: str, suspect_id: str):
    sessions = _sessions()
    if session_id not in sessions:
        raise KeyError(f"Session '{session_id}' was not found")
    if suspect_id not in suspects:
        raise KeyError(f"Suspect '{suspect_id}' was not found")

    session = sessions[session_id]
    if session.get("status") != "active":
        raise ValueError("This game session has already ended")

    clue_count = len(set(session.get("discovered_clue_ids", [])))
    if clue_count < MINIMUM_CLUES_FOR_ACCUSATION:
        raise ValueError(
            f"At least {MINIMUM_CLUES_FOR_ACCUSATION} unique clues are required; "
            f"you currently have {clue_count}"
        )

    if session.get("accused_suspect_id") is not None:
        raise ValueError("An accusation has already been made")

    correct = bool(suspects[suspect_id]["is_guilty"])
    session["accused_suspect_id"] = suspect_id

    # Student 3 owns ending selection and final session lifecycle.
    # Record the result for Student 3; do not independently invent an ending here.
    session["accusation_correct"] = correct

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
        "status": session["status"],
    }
