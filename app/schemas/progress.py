
from pydantic import BaseModel, ConfigDict, Field, model_validator


class SessionCreate(BaseModel):
    """Data required to start a new player session."""

    model_config = ConfigDict(extra="forbid")

    player_name: str = Field(
        min_length=1,
        max_length=30,
        description="Name of the player"
    )


class SessionUpdate(BaseModel):
    """Fields the player is allowed to update."""

    model_config = ConfigDict(extra="forbid")

    player_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=30
    )

    @model_validator(mode="after")
    def validate_update(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")

        if self.player_name is None:
            raise ValueError("Player name cannot be null")

        return self


class ChoiceRequest(BaseModel):
    """The choice selected by the player."""

    model_config = ConfigDict(extra="forbid")

    choice_id: str = Field(
        min_length=1,
        description="ID of the selected story choice"
    )


class SessionOut(BaseModel):
    """Public information about a player session."""

    id: str
    player_name: str
    current_scene_id: str
    discovered_clue_ids: list[str]
    accused_suspect_id: str | None
    status: str
    ending_id: str | None
    choices_history: list[str]


class EndingOut(BaseModel):
    """Information about the ending reached by the player."""

    ending_id: str
    title: str
    description: str
