"""Business logic for login: check credentials and build the token."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core import config
from app.core.security import (
    DUMMY_HASH, create_access_token, verify_password
)
from app.models.user import User
from app.schemas.token import Token


def authenticate_user(db: Session, identifier: str, password: str) -> User | None:
    """Return the user if the email/username and password are correct.

    Returns None when the user does not exist OR the password is wrong. The
    caller must not say which one, so attackers cannot find out which emails
    are registered.
    """
    identifier = identifier.strip().lower()
    user = db.scalar(
        select(User).where(
            or_(
                func.lower(User.email) == identifier,
                func.lower(User.username) == identifier,
            )
        )
    )
    if user is None:
        # Do the same slow bcrypt work, so the response time is the same.
        verify_password(password, DUMMY_HASH)
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def login(db: Session, identifier: str, password: str) -> Token:
    """Log a user in and return a JWT.

    Raises:
        ValueError      - wrong credentials (router -> 401)
        PermissionError - account is deactivated (router -> 403)
    """
    user = authenticate_user(db, identifier, password)
    if user is None:
        raise ValueError("Incorrect email/username or password")
    if not user.is_active:
        raise PermissionError("Inactive account")
    return Token(
        access_token=create_access_token(user.id),
        token_type="bearer",
        expires_in=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
