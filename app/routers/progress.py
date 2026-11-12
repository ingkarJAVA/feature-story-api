
from fastapi import APIRouter, HTTPException, Response, status

from app.schemas.progress import (
    SessionCreate,
    SessionUpdate,
    SessionOut,
    ChoiceRequest,
    EndingOut
)

from app.services import progress_service


router = APIRouter(
    prefix="/api",
    tags=["Player Progress & Endings"]
)


@router.post(
    "/sessions",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED
)
def create_player_session(data: SessionCreate):
    """Start a new player session."""

    return progress_service.create_session(data.player_name)


@router.get(
    "/sessions/{session_id}",
    response_model=SessionOut
)
def get_player_session(session_id: str):
    """Get the current progress of a player."""

    try:
        return progress_service.get_session(session_id)
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.patch(
    "/sessions/{session_id}",
    response_model=SessionOut
)
def update_player_session(
    session_id: str,
    data: SessionUpdate
):
    """Update the player's information."""

    try:
        update_data = data.model_dump(exclude_unset=True)

        return progress_service.update_session(
            session_id,
            **update_data
        )

    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_player_session(session_id: str):
    """Delete a player session."""

    try:
        progress_service.delete_session(session_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.post(
    "/sessions/{session_id}/choices",
    response_model=SessionOut
)
def submit_player_choice(
    session_id: str,
    data: ChoiceRequest
):
    """Submit a choice and move to the next story scene."""

    try:
        return progress_service.make_choice(
            session_id,
            data.choice_id
        )

    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )


@router.get(
    "/sessions/{session_id}/ending",
    response_model=EndingOut
)
def get_player_ending(session_id: str):
    """Calculate and return the player's story ending."""

    try:
        return progress_service.get_ending(session_id)

    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error)
        )
