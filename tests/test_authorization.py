
"""Tests for authorization, resource ownership and role-based access."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def two_players(fresh_game_data, make_test_user):
    """Create two independent ordinary users."""

    owner = make_test_user("shrek")
    stranger = make_test_user("fiona")

    return owner, stranger


@pytest.fixture
def owned_session(client, two_players):
    """Create a session belonging to the first player."""

    owner, stranger = two_players

    response = client.post(
        "/api/sessions",
        json={"player_name": "Shrek"},
        headers=owner["headers"],
    )

    assert response.status_code == 201

    return response.json()


# ------------------------------------------------------------
# Authentication requirements
# ------------------------------------------------------------


def test_create_session_without_token_returns_401(
    client, fresh_game_data
):
    response = client.post(
        "/api/sessions",
        json={"player_name": "Shrek"},
    )

    assert response.status_code == 401


def test_create_session_with_invalid_token_returns_401(
    client, fresh_game_data
):
    response = client.post(
        "/api/sessions",
        json={"player_name": "Shrek"},
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_authenticated_user_can_create_session(
    client, two_players
):
    owner, _ = two_players

    response = client.post(
        "/api/sessions",
        json={"player_name": "Shrek"},
        headers=owner["headers"],
    )

    assert response.status_code == 201
    assert response.json()["user_id"] == owner["id"]


# ------------------------------------------------------------
# Protected session endpoints
# ------------------------------------------------------------


SESSION_OPERATIONS = [
    ("GET", "/api/sessions/{id}", None),

    ("PATCH", "/api/sessions/{id}",
     {"player_name": "Changed"}),

    ("DELETE", "/api/sessions/{id}", None),

    ("POST", "/api/sessions/{id}/choices",
     {"choice_id": "choice_1"}),

    ("GET", "/api/sessions/{id}/ending", None),

    ("POST", "/api/investigations/{id}/discover",
     {"clue_id": "poisoned_wine_glass"}),

    ("POST", "/api/investigations/{id}/accuse",
     {"suspect_id": "prince_charming"}),
]


@pytest.mark.parametrize(
    "method,path,payload", SESSION_OPERATIONS
)
def test_protected_endpoints_without_token(
    client, owned_session, method, path, payload
):
    response = client.request(
        method,
        path.format(id=owned_session["id"]),
        json=payload,
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "method,path,payload", SESSION_OPERATIONS
)
def test_other_user_cannot_access_session(
    client, two_players, owned_session,
    method, path, payload
):
    owner, stranger = two_players

    response = client.request(
        method,
        path.format(id=owned_session["id"]),
        json=payload,
        headers=stranger["headers"],
    )

    assert response.status_code == 403

    # Verify that the forbidden request did not change progress.
    check = client.get(
        f"/api/sessions/{owned_session['id']}",
        headers=owner["headers"],
    )

    assert check.status_code == 200
    assert check.json() == owned_session


# ------------------------------------------------------------
# Owner permissions
# ------------------------------------------------------------


def test_owner_can_read_session(
    client, two_players, owned_session
):
    owner, _ = two_players

    response = client.get(
        f"/api/sessions/{owned_session['id']}",
        headers=owner["headers"],
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == owner["id"]


def test_owner_can_update_session(
    client, two_players, owned_session
):
    owner, _ = two_players

    response = client.patch(
        f"/api/sessions/{owned_session['id']}",
        json={"player_name": "Donkey"},
        headers=owner["headers"],
    )

    assert response.status_code == 200
    assert response.json()["player_name"] == "Donkey"
    assert response.json()["user_id"] == owner["id"]


def test_owner_can_delete_session(
    client, two_players, owned_session
):
    owner, _ = two_players

    path = f"/api/sessions/{owned_session['id']}"

    response = client.delete(
        path,
        headers=owner["headers"],
    )

    assert response.status_code == 204

    assert client.get(
        path,
        headers=owner["headers"],
    ).status_code == 404


def test_owner_can_make_choice(
    client, two_players, owned_session
):
    owner, _ = two_players

    response = client.post(
        f"/api/sessions/{owned_session['id']}/choices",
        json={"choice_id": "choice_1"},
        headers=owner["headers"],
    )

    assert response.status_code == 200
    assert response.json()["current_scene_id"] == "scene_2"


def test_nonexistent_session_returns_404(
    client, two_players
):
    owner, _ = two_players

    response = client.get(
        "/api/sessions/unknown_session",
        headers=owner["headers"],
    )

    assert response.status_code == 404


# ------------------------------------------------------------
# Prevent ownership manipulation
# ------------------------------------------------------------


def test_cannot_create_session_for_another_user(
    client, two_players
):
    owner, stranger = two_players

    response = client.post(
        "/api/sessions",
        json={
            "player_name": "Shrek",
            "user_id": stranger["id"],
        },
        headers=owner["headers"],
    )

    assert response.status_code == 422


def test_cannot_change_session_owner(
    client, two_players, owned_session
):
    owner, stranger = two_players

    response = client.patch(
        f"/api/sessions/{owned_session['id']}",
        json={"user_id": stranger["id"]},
        headers=owner["headers"],
    )

    assert response.status_code == 422


def test_legacy_session_without_owner_is_forbidden(
    client, two_players, owned_session
):
    from sqlalchemy import text
    from app.database import SessionLocal

    owner, _ = two_players

    with SessionLocal() as db:
        db.execute(
            text(
                "UPDATE game_sessions SET user_id = NULL "
                "WHERE id = :session_id"
            ),
            {"session_id": owned_session["id"]},
        )
        db.commit()

    response = client.get(
        f"/api/sessions/{owned_session['id']}",
        headers=owner["headers"],
    )

    assert response.status_code == 403


# ------------------------------------------------------------
# Administrative permissions
# ------------------------------------------------------------


ADMIN_OPERATIONS = [
    (
        "POST", "/api/scenes",
        {"title": "New Scene", "description": "Test scene"},
    ),
    (
        "PATCH", "/api/scenes/scene_1",
        {"title": "Changed"},
    ),
    (
        "DELETE", "/api/scenes/scene_2", None,
    ),
    (
        "POST", "/api/scenes/scene_1/choices",
        {
            "choice_text": "New choice",
            "next_scene_id": "scene_2",
        },
    ),
    (
        "PATCH", "/api/choices/choice_1",
        {"choice_text": "Changed"},
    ),
    (
        "DELETE", "/api/choices/choice_1", None,
    ),
    (
        "POST", "/api/suspects",
        {
            "id": "gingy",
            "name": "Gingy",
            "description": "A gingerbread man.",
            "motive": "Unknown",
            "alibi": "In the kitchen",
        },
    ),
    (
        "PATCH", "/api/suspects/prince_charming",
        {"motive": "Changed"},
    ),
    (
        "DELETE", "/api/suspects/prince_charming", None,
    ),
    (
        "POST", "/api/clues",
        {
            "id": "new_clue",
            "name": "New Clue",
            "description": "A brand new clue.",
            "location": "Kitchen",
            "related_scene_id": "scene_3",
            "importance": "low",
        },
    ),
    (
        "PATCH", "/api/clues/secret_passage",
        {"importance": "low"},
    ),
    (
        "DELETE", "/api/clues/secret_passage", None,
    ),
]


@pytest.mark.parametrize(
    "method,path,payload", ADMIN_OPERATIONS
)
def test_admin_endpoints_require_authentication(
    client, fresh_game_data, method, path, payload
):
    response = client.request(
        method,
        path,
        json=payload,
    )

    assert response.status_code == 401


@pytest.mark.parametrize(
    "method,path,payload", ADMIN_OPERATIONS
)
def test_regular_user_cannot_modify_shared_content(
    client, two_players, method, path, payload
):
    owner, _ = two_players

    response = client.request(
        method,
        path,
        json=payload,
        headers=owner["headers"],
    )

    assert response.status_code == 403


def test_admin_can_create_scene(client, admin_user):
    response = client.post(
        "/api/scenes",
        json={
            "title": "Admin Scene",
            "description": "Created by an administrator.",
        },
        headers=admin_user["headers"],
    )

    assert response.status_code == 201


def test_admin_can_update_scene(client, admin_user):
    response = client.patch(
        "/api/scenes/scene_1",
        json={"title": "Updated by admin"},
        headers=admin_user["headers"],
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated by admin"


def test_admin_can_delete_scene(client, admin_user):
    created = client.post(
        "/api/scenes",
        json={
            "title": "Temporary",
            "description": "Will be deleted",
        },
        headers=admin_user["headers"],
    )

    assert created.status_code == 201

    response = client.delete(
        f"/api/scenes/{created.json()['id']}",
        headers=admin_user["headers"],
    )

    assert response.status_code == 204


def test_admin_cannot_access_another_players_session(
    client, two_players, owned_session, make_test_user
):
    admin = make_test_user("administrator", role="admin")

    response = client.get(
        f"/api/sessions/{owned_session['id']}",
        headers=admin["headers"],
    )

    assert response.status_code == 403


# ------------------------------------------------------------
# Public endpoints
# ------------------------------------------------------------


@pytest.mark.parametrize("path", [
    "/api/story",
    "/api/scenes",
    "/api/scenes/scene_1",
    "/api/scenes/scene_1/choices",
    "/api/suspects",
    "/api/suspects/prince_charming",
    "/api/clues",
    "/api/clues/secret_passage",
])
def test_public_endpoints_do_not_require_token(
    client, fresh_game_data, path
):
    response = client.get(path)

    assert response.status_code == 200
