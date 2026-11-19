"""Business logic for the Story & Scenes module (PostgreSQL version).

Every function receives a SQLAlchemy session `db` from the router.
When a rule is broken, we raise HTTPException with a status code:
    404 - something does not exist
    409 - the operation conflicts with the current data
    422 - the data is invalid (for example a choice points to a missing scene)
"""
from fastapi import HTTPException, status
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.story import Choice, Scene, Story
from app.schemas.story import ChoiceCreate, ChoiceUpdate, SceneCreate, SceneUpdate

DEFAULT_STORY_ID = "story_1"

# Sort "scene_2" before "scene_10": shorter IDs first, then alphabetical.
_NUMERIC_ORDER = (func.length(Scene.id), Scene.id)
_CHOICE_ORDER = (func.length(Choice.id), Choice.id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_id(db: Session, kind: str) -> str:
    """Create the next free ID such as scene_16 or choice_31.

    The number comes from a PostgreSQL sequence, so it is unique across
    restarts and concurrent requests, and is never reused.
    """
    model = Scene if kind == "scene" else Choice
    while True:
        number = db.execute(text(f"SELECT nextval('{kind}_id_seq')")).scalar_one()
        new_id = f"{kind}_{number}"
        # Skip IDs already taken by a custom ID (for example scene_20).
        if db.get(model, new_id) is None:
            return new_id


def _get_scene_or_404(db: Session, scene_id: str) -> Scene:
    scene = db.get(Scene, scene_id)
    if scene is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scene '{scene_id}' not found",
        )
    return scene


def _get_choice_or_404(db: Session, choice_id: str) -> Choice:
    choice = db.get(Choice, choice_id)
    if choice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Choice '{choice_id}' not found",
        )
    return choice


def _check_destination_exists(db: Session, next_scene_id: str) -> None:
    if db.get(Scene, next_scene_id) is None:
        raise HTTPException(
            status_code=422,
            detail=f"Destination scene '{next_scene_id}' does not exist",
        )


# ---------------------------------------------------------------------------
# Story
# ---------------------------------------------------------------------------

def get_story(db: Session) -> dict:
    story = db.get(Story, DEFAULT_STORY_ID)
    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Story not found. Run 'python -m app.seed' to load the data.",
        )
    # total_scenes is calculated from the database every time.
    total = db.execute(
        select(func.count()).select_from(Scene).where(Scene.story_id == story.id)
    ).scalar_one()
    return {
        "id": story.id,
        "title": story.title,
        "description": story.description,
        "genre": story.genre,
        "main_character": story.main_character,
        "total_scenes": total,
    }


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------

def list_scenes(db: Session) -> list:
    return list(db.scalars(select(Scene).order_by(*_NUMERIC_ORDER)))


def get_scene(db: Session, scene_id: str) -> Scene:
    return _get_scene_or_404(db, scene_id)


def create_scene(db: Session, data: SceneCreate) -> Scene:
    scene_id = data.id
    if scene_id is None:
        scene_id = _new_id(db, "scene")
    elif db.get(Scene, scene_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scene '{scene_id}' already exists",
        )

    scene = Scene(
        id=scene_id,
        story_id=DEFAULT_STORY_ID,
        title=data.title,
        description=data.description,
        location=data.location,
        is_ending=data.is_ending,
    )
    db.add(scene)
    try:
        db.commit()
    except IntegrityError:
        # Two requests tried to create the same custom ID at the same time.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scene '{scene_id}' already exists",
        )
    return scene


def update_scene(db: Session, scene_id: str, data: SceneUpdate) -> Scene:
    scene = _get_scene_or_404(db, scene_id)
    # exclude_unset=True -> only the fields the client actually sent
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(scene, field, value)
    db.commit()
    return scene


def delete_scene(db: Session, scene_id: str) -> None:
    _get_scene_or_404(db, scene_id)

    # Rule: a scene cannot be deleted if a choice from ANOTHER scene points to it.
    pointing_here = list(
        db.scalars(
            select(Choice.id)
            .where(Choice.next_scene_id == scene_id, Choice.scene_id != scene_id)
            .order_by(func.length(Choice.id), Choice.id)
        )
    )
    if pointing_here:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Scene '{scene_id}' cannot be deleted because these choices "
                f"point to it: {', '.join(pointing_here)}"
            ),
        )

    # The scene's own outgoing choices disappear together with it.
    db.query(Choice).filter(Choice.scene_id == scene_id).delete(
        synchronize_session=False
    )
    db.query(Scene).filter(Scene.id == scene_id).delete(synchronize_session=False)
    try:
        db.commit()
    except IntegrityError:
        # Someone added a choice pointing here a moment ago.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Scene '{scene_id}' cannot be deleted because choices point to it",
        )


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

def list_choices(db: Session, scene_id: str) -> list:
    _get_scene_or_404(db, scene_id)
    return list(
        db.scalars(
            select(Choice).where(Choice.scene_id == scene_id).order_by(*_CHOICE_ORDER)
        )
    )


def create_choice(db: Session, scene_id: str, data: ChoiceCreate) -> Choice:
    _get_scene_or_404(db, scene_id)                    # source scene must exist
    _check_destination_exists(db, data.next_scene_id)  # destination must exist

    choice = Choice(
        id=_new_id(db, "choice"),
        scene_id=scene_id,
        choice_text=data.choice_text,
        next_scene_id=data.next_scene_id,
    )
    db.add(choice)
    db.commit()
    return choice


def update_choice(db: Session, choice_id: str, data: ChoiceUpdate) -> Choice:
    choice = _get_choice_or_404(db, choice_id)

    if data.next_scene_id is not None:
        _check_destination_exists(db, data.next_scene_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(choice, field, value)
    db.commit()
    return choice


def delete_choice(db: Session, choice_id: str) -> None:
    choice = _get_choice_or_404(db, choice_id)
    db.delete(choice)
    db.commit()
