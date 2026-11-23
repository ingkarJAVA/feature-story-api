"""Password hashing and JWT helpers.

Passwords:  hash_password() / verify_password()   (bcrypt)
Tokens:     create_access_token() / decode_access_token()   (PyJWT)

This file is used by BOTH registration (hash_password) and login
(verify_password, tokens), so the two always match.
"""
import base64
import hashlib
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core import config

TOKEN_TYPE = "access"


# ----------------------------------------------------------------- passwords
def _prepare(password: str) -> bytes:
    """Turn any password into a fixed 44-byte value before bcrypt.

    bcrypt can only read the first 72 bytes of a password (and newer versions
    raise an error for longer ones). Running the password through SHA-256 first
    removes that limit, so very long or non-English passwords never crash.
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(password: str) -> str:
    """Return a bcrypt hash that is safe to store in the database."""
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """True if the password matches the stored hash. Never raises."""
    try:
        return bcrypt.checkpw(
            _prepare(plain_password), hashed_password.encode("utf-8")
        )
    except ValueError:
        # The stored hash is not a valid bcrypt hash.
        return False


# A hash of a random value. Login compares against it when the user does not
# exist, so "unknown user" and "wrong password" take the same time.
DUMMY_HASH = hash_password("this-user-does-not-exist")


# ---------------------------------------------------------------------- JWT
def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT for one user.

    Claims inside the token:
        sub  - who the token belongs to (the user id, as text)
        type - "access" (so other kinds of tokens could never be accepted)
        iat  - when it was issued
        exp  - when it stops working
    """
    now = datetime.now(timezone.utc)
    if expires_delta is None:
        expires_delta = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "type": TOKEN_TYPE,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Check the signature and expiry, and return the payload.

    Raises:
        jwt.ExpiredSignatureError - the token is too old
        jwt.InvalidTokenError     - anything else wrong with the token
    """
    payload = jwt.decode(
        token,
        config.SECRET_KEY,
        algorithms=[config.ALGORITHM],  # only HS256 is accepted
        options={"require": ["exp", "sub"]},
    )
    if payload.get("type") != TOKEN_TYPE:
        raise jwt.InvalidTokenError("Wrong token type")
    return payload
