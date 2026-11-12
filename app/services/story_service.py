"""Business logic for the Story & Scenes module.

All rules live here. The router only calls these functions.
When a rule is broken, we raise HTTPException with a status code:
    404 - something does not exist
    409 - the operation conflicts with the current data
    422 - the data is invalid (for example a choice points to a missing scene)
"""
from app.data.story_data import *
from app.schemas.story import *

from fastapi import HTTPException, status

from app.data import story_data
from app.schemas.story import ChoiceCreate, ChoiceUpdate, SceneCreate, SceneUpdate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_id(kind: str, existing: dict) -> str:
    """Create the next free ID such as scene_16 or choice_31."""
    while True:
        story_data.COUNTERS[kind] += 1
        new_id = f"{kind}_{story_data.COUNTERS[kind]}"
        if new_id not in existing:
            return new_id


def _get_scene_or_404(scene_id: str) -> dict:
    scene = story_data.SCENES.get(scene_id)
    if scene is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scene '{scene_id}' not found",
        )
    return scene


def _get_choice_or_404(choice_id: str) -> dict:
    choice = story_data.CHOICES.get(choice_id)
    if choice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Choice '{choice_id}' not found",
        )
    return choice


def _check_destination_exists(next_scene_id: str) -> None:
    if next_scene_id not in story_data.SCENES:
        raise HTTPException(
            status_code=422,
            detail=f"Destination scene '{next_scene_id}' does not exist",
        )


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------

def get_story() -> dict:
    story = dict(story_data.STORY)
    story["total_scenes"] = len(story_data.SCENES)
    return story


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------

def list_scenes() -> list:
    return list(story_data.SCENES.values())


def get_scene(scene_id: str) -> dict:
    return _get_scene_or_404(scene_id)


def create_scene(data: SceneCreate) -> dict:
    scene_id = data.id
    if scene_id is None:
        scene_id = _new_id("scene", story_data.SCENES)
    elif scene_id in story_data.SCENES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scene '{scene_id}' already exists",
        )

    scene = {
        "id": scene_id,
        "title": data.title,
        "description": data.description,
        "location": data.location,
        "is_ending": data.is_ending,
    }
    story_data.SCENES[scene_id] = scene
    return scene


def update_scene(scene_id: str, data: SceneUpdate) -> dict:
    scene = _get_scene_or_404(scene_id)
    # exclude_unset=True -> only the fields the client actually sent
    scene.update(data.model_dump(exclude_unset=True))
    return scene


def delete_scene(scene_id: str) -> None:
    _get_scene_or_404(scene_id)

    # Rule: a scene cannot be deleted if a choice from ANOTHER scene points to it.
    pointing_here = [
        choice["id"]
        for choice in story_data.CHOICES.values()
        if choice["next_scene_id"] == scene_id and choice["scene_id"] != scene_id
    ]
    if pointing_here:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Scene '{scene_id}' cannot be deleted because these choices "
                f"point to it: {', '.join(pointing_here)}"
            ),
        )

    # The scene's own choices disappear together with it.
    own_choices = [
        choice_id
        for choice_id, choice in story_data.CHOICES.items()
        if choice["scene_id"] == scene_id
    ]
    for choice_id in own_choices:
        del story_data.CHOICES[choice_id]

    del story_data.SCENES[scene_id]


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

def list_choices(scene_id: str) -> list:
    _get_scene_or_404(scene_id)
    return [
        choice
        for choice in story_data.CHOICES.values()
        if choice["scene_id"] == scene_id
    ]


def create_choice(scene_id: str, data: ChoiceCreate) -> dict:
    _get_scene_or_404(scene_id)                    # source scene must exist
    _check_destination_exists(data.next_scene_id)  # destination must exist

    choice_id = _new_id("choice", story_data.CHOICES)
    choice = {
        "id": choice_id,
        "scene_id": scene_id,
        "choice_text": data.choice_text,
        "next_scene_id": data.next_scene_id,
    }
    story_data.CHOICES[choice_id] = choice
    return choice


def update_choice(choice_id: str, data: ChoiceUpdate) -> dict:
    choice = _get_choice_or_404(choice_id)

    if data.next_scene_id is not None:
        _check_destination_exists(data.next_scene_id)

    choice.update(data.model_dump(exclude_unset=True))
    return choice


def delete_choice(choice_id: str) -> None:
    _get_choice_or_404(choice_id)
    del story_data.CHOICES[choice_id]
