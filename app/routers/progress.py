
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.progress import (
    SessionCreate,
    SessionUpdate,
    SessionOut,
    ChoiceRequest,
    EndingOut,
)
from app.services import progress_service


router = APIRouter(
    prefix="/api",
    tags=["Player Progress & Endings"],
)


@router.post(
    "/sessions",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_player_session(
    data: SessionCreate,
    db: Session = Depends(get_db),
):
    """Start a new player session."""
    try:
        return progress_service.create_session(db, data.player_name)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionOut,
)
def get_player_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Get the current progress of a player."""
    try:
        return progress_service.get_session(db, session_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.patch(
    "/sessions/{session_id}",
    response_model=SessionOut,
)
def update_player_session(
    session_id: str,
    data: SessionUpdate,
    db: Session = Depends(get_db),
):
    """Update the player's information."""
    try:
        update_data = data.model_dump(exclude_unset=True)

        return progress_service.update_session(
            db,
            session_id,
            **update_data,
        )
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_player_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Delete a player session."""
    try:
        progress_service.delete_session(db, session_id)
        return Response(status_code=204)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


@router.post(
    "/sessions/{session_id}/choices",
    response_model=SessionOut,
)
def submit_player_choice(
    session_id: str,
    data: ChoiceRequest,
    db: Session = Depends(get_db),
):
    """Submit a choice and move to the next story scene."""
    try:
        return progress_service.make_choice(
            db,
            session_id,
            data.choice_id,
        )
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )


@router.get(
    "/sessions/{session_id}/ending",
    response_model=EndingOut,
)
def get_player_ending(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Calculate and return the player's ending."""
    try:
        return progress_service.get_ending(db, session_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        )
