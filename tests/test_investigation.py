"""Tests for the Investigation module (PostgreSQL test database).

Every test starts from a clean database that contains the original story,
suspects and clues. Sessions are created through the real API.

Run from the project root:  pytest tests/test_investigation.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import SessionLocal
from app.main import app


client = TestClient(app)

ALL_CLUES = [
    "poisoned_wine_glass", "broken_royal_seal", "missing_succession_document",
    "secret_passage", "charming_letter", "golden_fabric",
]


@pytest.fixture(autouse=True)
def fresh_data(admin_user):
    """Prepare the database and authenticate the test user."""

    client.headers.update(admin_user["headers"])

    yield

    client.headers.pop("Authorization", None)

def new_session(scene_id: str = "scene_1") -> str:
    """Create a session through the API and (optionally) move it to a scene."""
    response = client.post("/api/sessions", json={"player_name": "Shrek"})
    assert response.status_code == 201
    session_id = response.json()["id"]
    if scene_id != "scene_1":
        with SessionLocal() as db:
            db.execute(
                text("UPDATE game_sessions SET current_scene_id = :s WHERE id = :i"),
                {"s": scene_id, "i": session_id},
            )
            db.commit()
    return session_id


def give_clues(session_id: str, clue_ids: list[str]) -> None:
    """Put clues straight into the database (skips the scene rule)."""
    with SessionLocal() as db:
        for clue_id in clue_ids:
            db.execute(
                text("INSERT INTO discovered_clues (session_id, clue_id) "
                     "VALUES (:s, :c)"),
                {"s": session_id, "c": clue_id},
            )
        db.commit()


def discover(session_id: str, clue_id: str):
    return client.post(
        f"/api/investigations/{session_id}/discover", json={"clue_id": clue_id}
    )


def accuse(session_id: str, suspect_id: str):
    return client.post(
        f"/api/investigations/{session_id}/accuse", json={"suspect_id": suspect_id}
    )


# ------------------------------------------------------------------ clues
def test_list_clues_returns_six():
    response = client.get("/api/clues")
    assert response.status_code == 200
    assert sorted(c["id"] for c in response.json()) == sorted(ALL_CLUES)


def test_list_clues_filter_high():
    response = client.get("/api/clues?importance=high")
    assert response.status_code == 200
    assert len(response.json()) == 4
    assert all(c["importance"] == "high" for c in response.json())


def test_list_clues_filter_location():
    response = client.get("/api/clues?location=royal bedroom")
    assert {c["id"] for c in response.json()} == {
        "poisoned_wine_glass", "broken_royal_seal"
    }


def test_invalid_clue_importance_returns_422():
    assert client.get("/api/clues?importance=urgent").status_code == 422


def test_get_clue():
    response = client.get("/api/clues/secret_passage")
    assert response.status_code == 200
    assert response.json()["related_scene_id"] == "scene_9"


def test_missing_clue_returns_404():
    assert client.get("/api/clues/not_real").status_code == 404


# --------------------------------------------------------------- suspects
def test_list_suspects_does_not_expose_guilt():
    response = client.get("/api/suspects")
    assert response.status_code == 200
    assert len(response.json()) == 3
    assert all("is_guilty" not in s for s in response.json())


def test_get_suspect():
    response = client.get("/api/suspects/prince_charming")
    assert response.status_code == 200
    assert response.json()["name"] == "Prince Charming"


def test_missing_suspect_returns_404():
    assert client.get("/api/suspects/not_real").status_code == 404


# --------------------------------------------------------------- discover
def test_discover_clue_success():
    session_id = new_session("scene_2")
    response = discover(session_id, "poisoned_wine_glass")
    assert response.status_code == 201
    assert response.json()["id"] == "poisoned_wine_glass"
    # Student 3's session endpoint now sees the clue from the database.
    session = client.get(f"/api/sessions/{session_id}").json()
    assert session["discovered_clue_ids"] == ["poisoned_wine_glass"]


def test_discover_same_clue_twice_returns_409():
    session_id = new_session("scene_2")
    assert discover(session_id, "poisoned_wine_glass").status_code == 201
    assert discover(session_id, "poisoned_wine_glass").status_code == 409


def test_discover_missing_session_returns_404():
    assert discover("session_999", "poisoned_wine_glass").status_code == 404


def test_discover_missing_clue_returns_404():
    session_id = new_session("scene_2")
    assert discover(session_id, "not_real").status_code == 404


def test_discover_clue_in_wrong_scene_returns_409():
    session_id = new_session("scene_1")
    assert discover(session_id, "poisoned_wine_glass").status_code == 409


def test_discover_in_completed_session_returns_409():
    session_id = new_session("scene_2")
    with SessionLocal() as db:
        db.execute(text("UPDATE game_sessions SET status='completed' WHERE id=:i"),
                   {"i": session_id})
        db.commit()
    assert discover(session_id, "poisoned_wine_glass").status_code == 409


def test_discover_empty_body_returns_422():
    session_id = new_session("scene_2")
    response = client.post(f"/api/investigations/{session_id}/discover", json={})
    assert response.status_code == 422


def test_two_clues_in_same_scene_can_both_be_discovered():
    session_id = new_session("scene_2")
    assert discover(session_id, "poisoned_wine_glass").status_code == 201
    assert discover(session_id, "broken_royal_seal").status_code == 201


# ----------------------------------------------------------------- accuse
def test_accuse_with_fewer_than_three_clues_returns_409():
    session_id = new_session()
    give_clues(session_id, ALL_CLUES[:2])
    assert accuse(session_id, "prince_charming").status_code == 409


def test_accuse_missing_suspect_returns_404():
    session_id = new_session()
    give_clues(session_id, ALL_CLUES[:3])
    assert accuse(session_id, "not_real").status_code == 404


def test_accuse_missing_session_returns_404():
    assert accuse("session_999", "prince_charming").status_code == 404


def test_accuse_correct_suspect():
    session_id = new_session()
    give_clues(session_id, ALL_CLUES[:3])
    response = accuse(session_id, "prince_charming")
    assert response.status_code == 200
    body = response.json()
    assert body["correct"] is True
    assert body["discovered_clue_count"] == 3
    assert body["status"] == "active"


def test_accuse_wrong_suspect():
    session_id = new_session()
    give_clues(session_id, ALL_CLUES[:3])
    body = accuse(session_id, "fairy_godmother").json()
    assert body["correct"] is False


def test_second_accusation_returns_409():
    session_id = new_session()
    give_clues(session_id, ALL_CLUES[:3])
    assert accuse(session_id, "prince_charming").status_code == 200
    assert accuse(session_id, "puss_in_boots").status_code == 409


def test_accusation_feeds_student3_ending():
    """Accuse the right suspect, reach the final scene, read the ending."""
    session_id = new_session()
    give_clues(session_id, ALL_CLUES[:3])
    assert accuse(session_id, "prince_charming").status_code == 200
    with SessionLocal() as db:
        db.execute(text("UPDATE game_sessions SET current_scene_id='scene_15' "
                        "WHERE id=:i"), {"i": session_id})
        db.commit()
    response = client.get(f"/api/sessions/{session_id}/ending")
    assert response.status_code == 200
    assert response.json()["ending_id"] == "true_detective"


def test_secret_ending_after_all_secret_clues():
    session_id = new_session()
    give_clues(session_id, ["secret_passage", "golden_fabric", "charming_letter"])
    assert accuse(session_id, "prince_charming").status_code == 200
    with SessionLocal() as db:
        db.execute(text("UPDATE game_sessions SET current_scene_id='scene_15' "
                        "WHERE id=:i"), {"i": session_id})
        db.commit()
    assert client.get(f"/api/sessions/{session_id}/ending").json()[
        "ending_id"] == "secret_ending"


# --------------------------------------------------- database relationships
def test_deleting_session_deletes_its_discovered_clues():
    session_id = new_session("scene_2")
    assert discover(session_id, "poisoned_wine_glass").status_code == 201
    assert client.delete(f"/api/sessions/{session_id}").status_code == 204
    with SessionLocal() as db:
        count = db.execute(
            text("SELECT count(*) FROM discovered_clues WHERE session_id=:i"),
            {"i": session_id},
        ).scalar_one()
    assert count == 0


def test_cannot_delete_clue_that_a_player_collected():
    session_id = new_session("scene_2")

    collected = discover(session_id, "poisoned_wine_glass")
    assert collected.status_code == 201, collected.text

    response = client.delete("/api/clues/poisoned_wine_glass")

    assert response.status_code == 409, response.text


def test_cannot_delete_suspect_that_was_accused():
    session_id = new_session()
    give_clues(session_id, ALL_CLUES[:3])
    accuse(session_id, "puss_in_boots")
    assert client.delete("/api/suspects/puss_in_boots").status_code == 409


def test_scene_has_multiple_clues_relationship():
    from app.models.story import Scene
    with SessionLocal() as db:
        scene = db.get(Scene, "scene_9")
        assert {c.id for c in scene.clues} == {"secret_passage", "golden_fabric"}


# ------------------------------------------------------------- clue CRUD
CLUE_PAYLOAD = {
    "id": "new_clue", "name": "New Clue", "description": "A brand new clue.",
    "location": "Kitchen", "related_scene_id": "scene_3", "importance": "low",
}


def test_create_clue():
    response = client.post("/api/clues", json=CLUE_PAYLOAD)
    assert response.status_code == 201
    assert client.get("/api/clues/new_clue").status_code == 200


def test_create_duplicate_clue_returns_409():
    payload = {**CLUE_PAYLOAD, "id": "poisoned_wine_glass"}
    assert client.post("/api/clues", json=payload).status_code == 409


def test_create_clue_with_missing_scene_returns_404():
    payload = {**CLUE_PAYLOAD, "related_scene_id": "scene_999"}
    assert client.post("/api/clues", json=payload).status_code == 404


def test_update_and_delete_clue():
    client.post("/api/clues", json=CLUE_PAYLOAD)
    response = client.patch("/api/clues/new_clue", json={"importance": "high"})
    assert response.status_code == 200
    assert response.json()["importance"] == "high"
    assert client.delete("/api/clues/new_clue").status_code == 204
    assert client.get("/api/clues/new_clue").status_code == 404


def test_update_missing_clue_returns_404():
    assert client.patch("/api/clues/nope", json={"importance": "low"}).status_code == 404


def test_create_update_delete_suspect():
    payload = {
        "id": "gingy", "name": "Gingy", "description": "A gingerbread man.",
        "motive": "Unknown", "alibi": "In the kitchen",
    }
    assert client.post("/api/suspects", json=payload).status_code == 201
    assert client.post("/api/suspects", json=payload).status_code == 409
    response = client.patch("/api/suspects/gingy", json={"motive": "Revenge"})
    assert response.json()["motive"] == "Revenge"
    assert client.delete("/api/suspects/gingy").status_code == 204
