import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.investigation import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_data():
    from app.data.investigation_data import clues, suspects
    from app.data import investigation_data
    original_suspects = {
        "prince_charming": {
            "id": "prince_charming", "name": "Prince Charming",
            "description": "A prince who believes he deserves the throne.",
            "motive": "Harold planned to change succession.",
            "alibi": "Claims he remained in the grand hall.",
            "is_guilty": True,
        },
        "fairy_godmother": {
            "id": "fairy_godmother", "name": "Fairy Godmother",
            "description": "A powerful magical figure.",
            "motive": "Wanted to preserve influence.",
            "alibi": "Claims she was in her laboratory.",
            "is_guilty": False,
        },
        "puss_in_boots": {
            "id": "puss_in_boots", "name": "Puss in Boots",
            "description": "A skilled swordsman.",
            "motive": "Had an argument with Harold.",
            "alibi": "Claims he was in the stables.",
            "is_guilty": False,
        },
    }
    original_clues = {
        "poisoned_wine_glass": {"id":"poisoned_wine_glass","name":"The Wine Glass","description":"A glass with traces of magical substance.","location":"Royal Bedroom","related_scene_id":"scene_2","importance":"high"},
        "broken_royal_seal": {"id":"broken_royal_seal","name":"Broken Royal Seal","description":"The king's seal is damaged.","location":"Royal Bedroom","related_scene_id":"scene_2","importance":"medium"},
        "missing_succession_document": {"id":"missing_succession_document","name":"Succession Document","description":"A document about royal succession.","location":"Royal Library","related_scene_id":"scene_7","importance":"high"},
        "secret_passage": {"id":"secret_passage","name":"Secret Passage","description":"A concealed passage in the castle.","location":"Castle Corridor","related_scene_id":"scene_9","importance":"high"},
        "charming_letter": {"id":"charming_letter","name":"Charming's Letter","description":"A letter revealing Charming's plans.","location":"Prince's Chamber","related_scene_id":"scene_10","importance":"high"},
        "golden_fabric": {"id":"golden_fabric","name":"Golden Fabric","description":"A torn piece of golden fabric.","location":"Secret Passage","related_scene_id":"scene_9","importance":"medium"},
    }
    suspects.clear(); suspects.update(original_suspects)
    clues.clear(); clues.update(original_clues)


def test_list_suspects_does_not_expose_guilt():
    response = client.get("/api/suspects")
    assert response.status_code == 200
    assert len(response.json()) >= 3
    assert "is_guilty" not in response.json()[0]


def test_list_clues_filter_high():
    response = client.get("/api/clues?importance=high")
    assert response.status_code == 200
    assert all(item["importance"] == "high" for item in response.json())


def test_missing_suspect_returns_404():
    assert client.get("/api/suspects/not_real").status_code == 404


def test_invalid_clue_importance_returns_422():
    assert client.get("/api/clues?importance=urgent").status_code == 422


def test_create_duplicate_clue_returns_409():
    payload = {
        "id": "poisoned_wine_glass", "name": "Duplicate",
        "description": "This is a duplicate clue.", "location": "Room",
        "related_scene_id": "scene_2", "importance": "low"
    }
    assert client.post("/api/clues", json=payload).status_code == 409
