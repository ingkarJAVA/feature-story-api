"""Pydantic models (schemas) for the Story & Scenes module.

Request models check the data the client sends.
Response models describe the JSON the API sends back.
"""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------

class StoryResponse(BaseModel):
    id: str
    title: str
    description: str
    genre: str
    main_character: str
    total_scenes: int


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------

class SceneCreate(BaseModel):
    """Body for POST /api/scenes.

    `id` is optional. If it is missing, the server creates the next free ID
    (for example scene_16).
    """

    # Remove spaces around text, so "   " becomes "" and fails min_length=1.
    # extra="forbid" rejects unknown fields (helps to catch typos).
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: Optional[str] = Field(default=None, pattern=r"^scene_\d+$")
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1)
    location: str = Field(default="Unknown", min_length=1, max_length=100)
    is_ending: bool = False


class SceneUpdate(BaseModel):
    """Body for PATCH /api/scenes/{scene_id}. Send only the fields to change."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, min_length=1)
    location: Optional[str] = Field(default=None, min_length=1, max_length=100)
    is_ending: Optional[bool] = None

    @model_validator(mode="after")
    def check_fields(self):
        if not self.model_fields_set:
            raise ValueError("Send at least one field to update")
        for name in self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class SceneResponse(BaseModel):
    id: str
    title: str
    description: str
    location: str
    is_ending: bool


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

class ChoiceCreate(BaseModel):
    """Body for POST /api/scenes/{scene_id}/choices.

    The source scene comes from the URL, so it is not in the body.
    """

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    choice_text: str = Field(min_length=1, max_length=200)
    next_scene_id: str = Field(min_length=1)


class ChoiceUpdate(BaseModel):
    """Body for PATCH /api/choices/{choice_id}. Send only the fields to change."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    choice_text: Optional[str] = Field(default=None, min_length=1, max_length=200)
    next_scene_id: Optional[str] = Field(default=None, min_length=1)

    @model_validator(mode="after")
    def check_fields(self):
        if not self.model_fields_set:
            raise ValueError("Send at least one field to update")
        for name in self.model_fields_set:
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


class ChoiceResponse(BaseModel):
    id: str
    scene_id: str
    choice_text: str
    next_scene_id: str
