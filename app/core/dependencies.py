"""Reusable authentication dependency: get_current_user().

Use it in any router to protect an endpoint:

    from app.core.dependencies import get_current_user
    from app.models.user import User

    @router.get("/something")
    def something(current_user: User = Depends(get_current_user)):
        ...
"""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

# Reads the "Authorization: Bearer <token>" header. The tokenUrl makes the
# green "Authorize" button in Swagger (/docs) log in through POST /auth/login.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Return the logged-in user, or raise an HTTP error.

    401 - no token / invalid token / expired token / user no longer exists
    403 - the account is deactivated
    """
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token has expired")
    except jwt.InvalidTokenError:
        raise _unauthorized("Invalid token")

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise _unauthorized("Invalid token")

    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized("User no longer exists")
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account"
        )
    return user
