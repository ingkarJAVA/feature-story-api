from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


Importance = Literal["low", "medium", "high"]


class SuspectCreate(BaseModel):
    id: str = Field(min_length=2, max_length=50, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=5, max_length=500)
    motive: str = Field(min_length=3, max_length=300)
    alibi: str = Field(min_length=3, max_length=300)
    is_guilty: bool = False


class SuspectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    description: str | None = Field(default=None, min_length=5, max_length=500)
    motive: str | None = Field(default=None, min_length=3, max_length=300)
    alibi: str | None = Field(default=None, min_length=3, max_length=300)


class SuspectOut(BaseModel):
    id: str
    name: str
    description: str
    motive: str
    alibi: str
    model_config = ConfigDict(from_attributes=True)


class ClueCreate(BaseModel):
    id: str = Field(min_length=2, max_length=60, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=5, max_length=600)
    location: str = Field(min_length=2, max_length=100)
    related_scene_id: str = Field(min_length=2, max_length=50)
    importance: Importance


class ClueUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, min_length=5, max_length=600)
    location: str | None = Field(default=None, min_length=2, max_length=100)
    related_scene_id: str | None = Field(default=None, min_length=2, max_length=50)
    importance: Importance | None = None


class ClueOut(BaseModel):
    id: str
    name: str
    description: str
    location: str
    related_scene_id: str
    importance: Importance


class DiscoverClueRequest(BaseModel):
    clue_id: str = Field(min_length=2, max_length=60)


class AccusationRequest(BaseModel):
    suspect_id: str = Field(min_length=2, max_length=50)


class AccusationResponse(BaseModel):
    session_id: str
    suspect_id: str
    correct: bool
    message: str
    discovered_clue_count: int
    status: Literal["active", "completed"]
