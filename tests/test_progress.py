
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data.progress_data import sessions, reset_sessions


client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_sessions():
    """Reset player sessions before and after each test."""
    reset_sessions()
    yield
    reset_sessions()


def test_create_session():
    """A player can create a new session."""

    response = client.post(
        "/api/sessions",
        json={"player_name": "Shrek"}
    )

    assert response.status_code == 201
    assert response.json()["player_name"] == "Shrek"
    assert response.json()["current_scene_id"] == "scene_1"
    assert response.json()["status"] == "active"


def test_create_session_with_invalid_name():
    """An empty player name must be rejected."""

    response = client.post(
        "/api/sessions",
        json={"player_name": ""}
    )

    assert response.status_code == 422


def test_get_session():
    """A player can retrieve their session."""

    created = client.post(
        "/api/sessions",
        json={"player_name": "Shrek"}
    )

    session_id = created.json()["id"]

    response = client.get(f"/api/sessions/{session_id}")

    assert response.status_code == 200
    assert response.json()["id"] == session_id


def test_get_nonexistent_session():
    """An unknown session must return 404."""

    response = client.get("/api/sessions/unknown_session")

    assert response.status_code == 404


def test_update_session():
    """A player can update their name."""

    created = client.post(
        "/api/sessions",
        json={"player_name": "Shrek"}
    )

    session_id = created.json()["id"]

    response = client.patch(
        f"/api/sessions/{session_id}",
        json={"player_name": "Donkey"}
    )

    assert response.status_code == 200
    assert response.json()["player_name"] == "Donkey"


def test_delete_session():
    """A player can delete their session."""

    created = client.post(
        "/api/sessions",
        json={"player_name": "Shrek"}
    )

    session_id = created.json()["id"]

    response = client.delete(f"/api/sessions/{session_id}")

    assert response.status_code == 204

    check = client.get(f"/api/sessions/{session_id}")

    assert check.status_code == 404


def test_make_valid_choice():
    """A valid choice moves the player to the next scene."""

    created = client.post(
        "/api/sessions",
        json={"player_name": "Shrek"}
    )

    session_id = created.json()["id"]

    response = client.post(
        f"/api/sessions/{session_id}/choices",
        json={"choice_id": "choice_1"}
    )

    assert response.status_code == 200
    assert response.json()["current_scene_id"] == "scene_2"
    assert "choice_1" in response.json()["choices_history"]


def test_reject_choice_from_another_scene():
    """A player cannot select a choice from another scene."""

    created = client.post(
        "/api/sessions",
        json={"player_name": "Shrek"}
    )

    session_id = created.json()["id"]

    response = client.post(
        f"/api/sessions/{session_id}/choices",
        json={"choice_id": "choice_3"}
    )

    assert response.status_code == 409


def test_ending_before_final_scene():
    """The ending cannot be requested before the final scene."""

    created = client.post(
        "/api/sessions",
        json={"player_name": "Shrek"}
    )

    session_id = created.json()["id"]

    response = client.get(
        f"/api/sessions/{session_id}/ending"
    )

    assert response.status_code == 409


def test_get_ending_completes_session():
    """Reaching the final scene allows the player to get an ending."""

    created = client.post(
        "/api/sessions",
        json={"player_name": "Shrek"}
    )

    session_id = created.json()["id"]

    # Prepare the session as if the player reached the final scene
    # and correctly accused the murderer.
    sessions[session_id]["current_scene_id"] = "scene_15"
    sessions[session_id]["accusation_correct"] = True

    response = client.get(
        f"/api/sessions/{session_id}/ending"
    )

    assert response.status_code == 200
    assert response.json()["ending_id"] == "true_detective"

    # Verify that the session was completed.
    check = client.get(f"/api/sessions/{session_id}")

    assert check.status_code == 200
    assert check.json()["status"] == "completed"
    assert check.json()["ending_id"] == "true_detective"
