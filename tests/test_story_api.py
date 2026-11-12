"""Tests for the Story & Scenes module.

The tests build a tiny FastAPI app that only includes our router, so they run
without the other students' code. (This is only for testing - the real
project has one shared app in main.py.)

Run from the project root:  pytest -v
"""
from app.main import app

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.data import story_data
from app.routers import story

app_for_tests = FastAPI()
app_for_tests.include_router(story.router)


@pytest.fixture(autouse=True)
def fresh_data():
    """Reset the in-memory data before every test so tests don't affect each other."""
    story_data.reset_data()


@pytest.fixture
def client():
    return TestClient(app_for_tests)


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------

def test_get_story(client):
    response = client.get("/api/story")
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Shrek: Who Killed the King?"
    assert body["main_character"] == "Shrek"
    assert body["total_scenes"] == 15


def test_story_total_scenes_updates_after_create(client):
    client.post("/api/scenes", json={"title": "Bonus", "description": "Extra scene"})
    assert client.get("/api/story").json()["total_scenes"] == 16


# ---------------------------------------------------------------------------
# Scenes - read
# ---------------------------------------------------------------------------

def test_get_all_scenes(client):
    response = client.get("/api/scenes")
    assert response.status_code == 200
    scenes = response.json()
    assert len(scenes) == 15
    assert scenes[0]["id"] == "scene_1"
    assert scenes[-1]["is_ending"] is True


def test_get_scene_by_id(client):
    response = client.get("/api/scenes/scene_2")
    assert response.status_code == 200
    assert response.json()["title"] == "The Crime Scene"


def test_get_missing_scene_returns_404(client):
    response = client.get("/api/scenes/scene_999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Scenes - create
# ---------------------------------------------------------------------------

def test_create_scene_generates_id(client):
    response = client.post(
        "/api/scenes",
        json={"title": "The Dragon's Keep", "description": "A fiery surprise.", "location": "Keep"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "scene_16"
    assert body["is_ending"] is False
    assert client.get("/api/scenes/scene_16").status_code == 200


def test_create_scene_with_custom_id(client):
    response = client.post(
        "/api/scenes",
        json={"id": "scene_50", "title": "Custom", "description": "Custom scene"},
    )
    assert response.status_code == 201
    assert response.json()["id"] == "scene_50"


def test_create_scene_with_duplicate_id_returns_409(client):
    response = client.post(
        "/api/scenes",
        json={"id": "scene_1", "title": "Copy", "description": "Duplicate"},
    )
    assert response.status_code == 409


def test_create_scene_with_empty_title_returns_422(client):
    response = client.post("/api/scenes", json={"title": "", "description": "Text"})
    assert response.status_code == 422


def test_create_scene_with_blank_description_returns_422(client):
    response = client.post("/api/scenes", json={"title": "Title", "description": "   "})
    assert response.status_code == 422


def test_create_scene_missing_fields_returns_422(client):
    response = client.post("/api/scenes", json={"title": "Only a title"})
    assert response.status_code == 422


def test_create_scene_with_bad_id_format_returns_422(client):
    response = client.post(
        "/api/scenes", json={"id": "abc", "title": "T", "description": "D"}
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Scenes - update
# ---------------------------------------------------------------------------

def test_update_scene(client):
    response = client.patch("/api/scenes/scene_1", json={"title": "A Very Unexpected Visitor"})
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "A Very Unexpected Visitor"
    assert body["location"] == "Shrek's Swamp"  # untouched field stays the same


def test_update_missing_scene_returns_404(client):
    response = client.patch("/api/scenes/scene_999", json={"title": "Nope"})
    assert response.status_code == 404


def test_update_scene_with_empty_title_returns_422(client):
    response = client.patch("/api/scenes/scene_1", json={"title": ""})
    assert response.status_code == 422


def test_update_scene_with_empty_body_returns_422(client):
    response = client.patch("/api/scenes/scene_1", json={})
    assert response.status_code == 422


def test_update_scene_with_null_title_returns_422(client):
    response = client.patch("/api/scenes/scene_1", json={"title": None})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Scenes - delete
# ---------------------------------------------------------------------------

def test_delete_scene_without_incoming_choices(client):
    created = client.post(
        "/api/scenes", json={"title": "Temp", "description": "Will be deleted"}
    ).json()
    response = client.delete(f"/api/scenes/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/api/scenes/{created['id']}").status_code == 404


def test_delete_scene_with_incoming_choice_returns_409(client):
    # scene_2 is the destination of choice_1 (from scene_1)
    response = client.delete("/api/scenes/scene_2")
    assert response.status_code == 409
    assert client.get("/api/scenes/scene_2").status_code == 200


def test_delete_scene_removes_its_own_choices(client):
    created = client.post(
        "/api/scenes", json={"title": "Temp", "description": "Has a choice"}
    ).json()
    choice = client.post(
        f"/api/scenes/{created['id']}/choices",
        json={"choice_text": "Run away", "next_scene_id": "scene_1"},
    ).json()
    assert client.delete(f"/api/scenes/{created['id']}").status_code == 204
    assert choice["id"] not in story_data.CHOICES


def test_delete_missing_scene_returns_404(client):
    assert client.delete("/api/scenes/scene_999").status_code == 404


# ---------------------------------------------------------------------------
# Choices - read
# ---------------------------------------------------------------------------

def test_get_choices_for_scene(client):
    response = client.get("/api/scenes/scene_1/choices")
    assert response.status_code == 200
    choices = response.json()
    assert len(choices) == 2
    assert all(c["scene_id"] == "scene_1" for c in choices)
    assert choices[0]["id"] == "choice_1"


def test_every_scene_except_the_ending_has_choices(client):
    for scene_number in range(1, 15):
        choices = client.get(f"/api/scenes/scene_{scene_number}/choices").json()
        assert len(choices) >= 2, f"scene_{scene_number} needs at least 2 choices"
    assert client.get("/api/scenes/scene_15/choices").json() == []


def test_all_initial_choices_point_to_existing_scenes(client):
    scene_ids = {s["id"] for s in client.get("/api/scenes").json()}
    for scene_id in scene_ids:
        for choice in client.get(f"/api/scenes/{scene_id}/choices").json():
            assert choice["next_scene_id"] in scene_ids


def test_get_choices_of_missing_scene_returns_404(client):
    assert client.get("/api/scenes/scene_999/choices").status_code == 404


# ---------------------------------------------------------------------------
# Choices - create
# ---------------------------------------------------------------------------

def test_create_choice_with_valid_destination(client):
    response = client.post(
        "/api/scenes/scene_1/choices",
        json={"choice_text": "Ask Donkey for help", "next_scene_id": "scene_8"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "choice_31"  # the seed data has choice_1 ... choice_30
    assert body["scene_id"] == "scene_1"
    assert body["next_scene_id"] == "scene_8"
    assert len(client.get("/api/scenes/scene_1/choices").json()) == 3


def test_create_choice_with_nonexistent_destination_returns_422(client):
    response = client.post(
        "/api/scenes/scene_1/choices",
        json={"choice_text": "Jump into the void", "next_scene_id": "scene_999"},
    )
    assert response.status_code == 422
    assert len(client.get("/api/scenes/scene_1/choices").json()) == 2


def test_create_choice_for_missing_source_scene_returns_404(client):
    response = client.post(
        "/api/scenes/scene_999/choices",
        json={"choice_text": "Hello", "next_scene_id": "scene_1"},
    )
    assert response.status_code == 404


def test_create_choice_with_empty_text_returns_422(client):
    response = client.post(
        "/api/scenes/scene_1/choices",
        json={"choice_text": "  ", "next_scene_id": "scene_2"},
    )
    assert response.status_code == 422


def test_create_choice_missing_fields_returns_422(client):
    response = client.post("/api/scenes/scene_1/choices", json={"choice_text": "No target"})
    assert response.status_code == 422


def test_choice_ids_are_never_reused(client):
    first = client.post(
        "/api/scenes/scene_1/choices",
        json={"choice_text": "One", "next_scene_id": "scene_2"},
    ).json()
    client.delete(f"/api/choices/{first['id']}")
    second = client.post(
        "/api/scenes/scene_1/choices",
        json={"choice_text": "Two", "next_scene_id": "scene_2"},
    ).json()
    assert second["id"] != first["id"]


# ---------------------------------------------------------------------------
# Choices - update and delete
# ---------------------------------------------------------------------------

def test_update_choice(client):
    response = client.patch(
        "/api/choices/choice_1",
        json={"choice_text": "Hurry to the castle", "next_scene_id": "scene_3"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["choice_text"] == "Hurry to the castle"
    assert body["next_scene_id"] == "scene_3"
    assert body["scene_id"] == "scene_1"


def test_update_choice_with_nonexistent_destination_returns_422(client):
    response = client.patch("/api/choices/choice_1", json={"next_scene_id": "scene_999"})
    assert response.status_code == 422
    assert story_data.CHOICES["choice_1"]["next_scene_id"] == "scene_2"


def test_update_choice_with_empty_text_returns_422(client):
    response = client.patch("/api/choices/choice_1", json={"choice_text": ""})
    assert response.status_code == 422


def test_update_missing_choice_returns_404(client):
    response = client.patch("/api/choices/choice_999", json={"choice_text": "Hi"})
    assert response.status_code == 404


def test_delete_choice(client):
    assert client.delete("/api/choices/choice_1").status_code == 204
    choices = client.get("/api/scenes/scene_1/choices").json()
    assert all(c["id"] != "choice_1" for c in choices)


def test_delete_missing_choice_returns_404(client):
    assert client.delete("/api/choices/choice_999").status_code == 404


def test_deleting_the_last_choice_into_a_scene_allows_deleting_the_scene(client):
    created = client.post(
        "/api/scenes", json={"title": "Detour", "description": "A side path"}
    ).json()
    choice = client.post(
        "/api/scenes/scene_1/choices",
        json={"choice_text": "Take the detour", "next_scene_id": created["id"]},
    ).json()

    assert client.delete(f"/api/scenes/{created['id']}").status_code == 409
    client.delete(f"/api/choices/{choice['id']}")
    assert client.delete(f"/api/scenes/{created['id']}").status_code == 204
