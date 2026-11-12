
from app.data.progress_data import sessions, generate_session_id
from app.data.story_data import SCENES, CHOICES


# Available endings in the detective story.
ENDINGS = {
    "true_detective": {
        "ending_id": "true_detective",
        "title": "The True Detective",
        "description": (
            "Shrek collected the evidence and correctly identified "
            "the murderer. The truth about King Harold's death is revealed."
        )
    },
    "wrong_suspect": {
        "ending_id": "wrong_suspect",
        "title": "The Wrong Accusation",
        "description": (
            "Shrek accused the wrong person. The real murderer "
            "remains free, and justice has not been served."
        )
    },
    "new_king": {
        "ending_id": "new_king",
        "title": "A New King",
        "description": (
            "The investigation ends without a correct accusation. "
            "The kingdom moves forward under a new ruler."
        )
    },
    "secret_ending": {
        "ending_id": "secret_ending",
        "title": "The Hidden Truth",
        "description": (
            "Shrek discovered the secret evidence and uncovered "
            "a hidden truth behind the king's death."
        )
    }
}


def create_session(player_name: str) -> dict:
    """Create a new player session."""

    session_id = generate_session_id()

    session = {
        "id": session_id,
        "player_name": player_name,
        "current_scene_id": "scene_1",
        "discovered_clue_ids": [],
        "accused_suspect_id": None,
        "accusation_correct": None,
        "status": "active",
        "ending_id": None,
        "choices_history": []
    }

    sessions[session_id] = session

    return session


def get_session(session_id: str) -> dict:
    """Return a session by its ID."""

    if session_id not in sessions:
        raise KeyError("Session not found")

    return sessions[session_id]


def update_session(session_id: str, player_name: str) -> dict:
    """Update the player's name."""

    session = get_session(session_id)

    if session["status"] != "active":
        raise ValueError("Cannot update a completed session")

    session["player_name"] = player_name

    return session


def delete_session(session_id: str) -> None:
    """Delete a player session."""

    get_session(session_id)
    del sessions[session_id]


def make_choice(session_id: str, choice_id: str) -> dict:
    """Process a player's choice and move to the next scene."""

    session = get_session(session_id)

    if session["status"] != "active":
        raise ValueError("This session is already completed")

    current_scene_id = session["current_scene_id"]
    current_scene = SCENES.get(current_scene_id)

    if current_scene is None:
        raise KeyError("Current scene not found")

    if current_scene.get("is_ending", False):
        raise ValueError("The player has already reached the final scene")

    choice = CHOICES.get(choice_id)

    if choice is None:
        raise KeyError("Choice not found")

    if choice["scene_id"] != current_scene_id:
        raise ValueError("This choice does not belong to the current scene")

    next_scene_id = choice["next_scene_id"]

    if next_scene_id not in SCENES:
        raise ValueError("The destination scene does not exist")

    session["choices_history"].append(choice_id)
    session["current_scene_id"] = next_scene_id

    return session


def determine_ending(session: dict) -> str:
    """Determine the ending using the player's investigation results."""

    discovered_clues = set(session["discovered_clue_ids"])

    secret_clues = {
        "secret_passage",
        "golden_fabric",
        "charming_letter"
    }

    # Discovering all three secret clues unlocks the secret ending.
    if secret_clues.issubset(discovered_clues):
        return "secret_ending"

    if session["accusation_correct"] is True:
        return "true_detective"

    if session["accusation_correct"] is False:
        return "wrong_suspect"

    # If the player reaches the end without a correct accusation,
    # the kingdom gets a new ruler.
    return "new_king"


def get_ending(session_id: str) -> dict:
    """Calculate and return the ending of a completed story."""

    session = get_session(session_id)

    # Allow the player to view an ending that was already calculated.
    if session["status"] == "completed":
        return ENDINGS[session["ending_id"]]

    current_scene = SCENES.get(session["current_scene_id"])

    if current_scene is None:
        raise KeyError("Current scene not found")

    if not current_scene.get("is_ending", False):
        raise ValueError("The story has not reached its final scene")

    ending_id = determine_ending(session)

    session["ending_id"] = ending_id
    session["status"] = "completed"

    return ENDINGS[ending_id]
