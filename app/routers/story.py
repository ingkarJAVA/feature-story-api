"""HTTP endpoints for the Story & Scenes module.

This file only receives requests and returns responses.
All the real logic is in app/services/story_service.py.
"""
from app.schemas.story import *
from app.services.story_service import *
from app.data.story_data import *

from typing import List

from fastapi import APIRouter, status

from app.schemas.story import (
    ChoiceCreate,
    ChoiceResponse,
    ChoiceUpdate,
    SceneCreate,
    SceneResponse,
    SceneUpdate,
    StoryResponse,
)
from app.services import story_service

router = APIRouter(prefix="/api", tags=["Story & Scenes"])


# --- Story -----------------------------------------------------------------

@router.get("/story", response_model=StoryResponse)
def get_story():
    return story_service.get_story()


# --- Scenes ----------------------------------------------------------------

@router.get("/scenes", response_model=List[SceneResponse])
def list_scenes():
    return story_service.list_scenes()


@router.get("/scenes/{scene_id}", response_model=SceneResponse)
def get_scene(scene_id: str):
    return story_service.get_scene(scene_id)


@router.post("/scenes", response_model=SceneResponse, status_code=status.HTTP_201_CREATED)
def create_scene(data: SceneCreate):
    return story_service.create_scene(data)


@router.patch("/scenes/{scene_id}", response_model=SceneResponse)
def update_scene(scene_id: str, data: SceneUpdate):
    return story_service.update_scene(scene_id, data)


@router.delete("/scenes/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scene(scene_id: str):
    story_service.delete_scene(scene_id)


# --- Choices ---------------------------------------------------------------

@router.get("/scenes/{scene_id}/choices", response_model=List[ChoiceResponse])
def list_choices(scene_id: str):
    return story_service.list_choices(scene_id)


@router.post(
    "/scenes/{scene_id}/choices",
    response_model=ChoiceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_choice(scene_id: str, data: ChoiceCreate):
    return story_service.create_choice(scene_id, data)


@router.patch("/choices/{choice_id}", response_model=ChoiceResponse)
def update_choice(choice_id: str, data: ChoiceUpdate):
    return story_service.update_choice(choice_id, data)


@router.delete("/choices/{choice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_choice(choice_id: str):
    story_service.delete_choice(choice_id)
