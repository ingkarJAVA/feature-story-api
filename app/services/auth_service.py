"""Business logic for registration and login."""

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import config
from app.core.security import (
    DUMMY_HASH,
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import UserRegister
from app.schemas.token import Token


# ================= REGISTRATION =================


class DuplicateUserError(ValueError):
    """The email or username is already used."""


def _exists(db: Session, column, value) -> bool:
    return db.scalar(
        select(User.id).where(column == value)
    ) is not None


def _duplicate_message(error: IntegrityError) -> str:
    diag = getattr(error.orig, "diag", None)
    constraint = getattr(diag, "constraint_name", None)

    if constraint == "uq_users_email":
        return "Email is already registered"

    if constraint in (
            "uq_users_username",
            "uq_users_username_lower",
    ):
        return "Username is already taken"

    return "Email or username is already in use"


def register_user(db: Session, data: UserRegister) -> User:

    if _exists(db, User.email, data.email):
        raise DuplicateUserError(
            "Email is already registered"
        )

    if _exists(
            db,
            func.lower(User.username),
            data.username.lower(),
    ):
        raise DuplicateUserError(
            "Username is already taken"
        )

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )

    db.add(user)

    try:
        db.commit()

    except IntegrityError as error:
        db.rollback()

        error_code = (
            getattr(error.orig, "sqlstate", None)
            or getattr(error.orig, "pgcode", None)
        )

        if error_code == "23505":
            raise DuplicateUserError(
                _duplicate_message(error)
            ) from None

        raise

    db.refresh(user)

    return user


# ================= LOGIN =================


def authenticate_user(
    db: Session,
    identifier: str,
    password: str,
) -> User | None:

    identifier = identifier.strip().lower()

    if "@" in identifier:
        query = select(User).where(
            func.lower(User.email) == identifier
        )
    else:
        query = select(User).where(
            func.lower(User.username) == identifier
        )

    users = db.scalars(query).all()

    if len(users) != 1:
        verify_password(password, DUMMY_HASH)
        return None

    user = users[0]

    if not verify_password(
        password,
        user.hashed_password,
    ):
        return None

    return user


def login(
    db: Session,
    identifier: str,
    password: str,
) -> Token:

    user = authenticate_user(
        db,
        identifier,
        password,
    )

    if user is None:
        raise ValueError(
            "Incorrect email/username or password"
        )

    if not user.is_active:
        raise PermissionError("Inactive account")

    return Token(
        access_token=create_access_token(user.id),
        token_type="bearer",
        expires_in=config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )