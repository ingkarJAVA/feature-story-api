"""Password hashing and JWT helpers."""

from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core import config


_password_hasher = PasswordHasher()

TOKEN_TYPE = "access"


def hash_password(password: str) -> str:
    """Return a secure Argon2id password hash."""
    return _password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Check whether the password matches the stored hash."""
    try:
        return _password_hasher.verify(
            hashed_password,
            plain_password,
        )
    except (VerificationError, InvalidHashError):
        return False


DUMMY_HASH = hash_password("this-user-does-not-exist")


def create_access_token(
    user_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token."""

    now = datetime.now(timezone.utc)

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    payload = {
        "sub": str(user_id),
        "type": TOKEN_TYPE,
        "iat": now,
        "exp": now + expires_delta,
    }

    return jwt.encode(
        payload,
        config.SECRET_KEY,
        algorithm=config.ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """Validate the JWT and return its payload."""

    payload = jwt.decode(
        token,
        config.SECRET_KEY,
        algorithms=[config.ALGORITHM],
        options={"require": ["exp", "sub"]},
    )

    if payload.get("type") != TOKEN_TYPE:
        raise jwt.InvalidTokenError("Wrong token type")

    return payload