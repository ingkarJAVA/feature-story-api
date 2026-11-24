"""Authorization dependencies for protected resources."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.progress import GameSession
from app.models.user import User


def require_session_owner(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GameSession:
    """Allow access only to the owner of a game session."""

    session = db.get(GameSession, session_id)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not own this game session",
        )

    return session


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Allow only administrators to modify shared content."""

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )

    return current_user