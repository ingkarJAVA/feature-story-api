"""Business logic for user registration (Assignment 7, Student 1).

Student 2 can add the login logic to this file or in a new service file.
"""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User
from app.schemas.auth import UserRegister
from psycopg.errors import UniqueViolation

# PostgreSQL error code for "unique constraint violated".
UNIQUE_VIOLATION = "23505"


class DuplicateUserError(ValueError):
    """The email or username is already used. The router turns it into 409."""


def _exists(db: Session, column, value) -> bool:
    return db.scalar(select(User.id).where(column == value)) is not None


def _duplicate_message(error: IntegrityError) -> str:
    """Pick a friendly message from the name of the violated constraint.

    Only our own short text is returned - never SQL or database details.
    """
    diag = getattr(error.orig, "diag", None)
    constraint = getattr(diag, "constraint_name", None)
    if constraint == "uq_users_email":
        return "Email is already registered"
    if constraint == "uq_users_username":
        return "Username is already taken"
    return "Email or username is already in use"


def register_user(db: Session, data: UserRegister) -> User:
    """Create a new user and return the saved User record.

    Raises DuplicateUserError if the email or username is already used.
    """
    # Fast, friendly checks first ...
    if _exists(db, User.email, data.email):
        raise DuplicateUserError("Email is already registered")
    if _exists(db, User.username, data.username):
        raise DuplicateUserError("Username is already taken")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    db.add(user)

    # ... but the UNIQUE constraints in the database are the real protection.
    # If two requests pass the checks above at the same moment, the second
    # commit fails here and we answer 409 instead of crashing.
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()

        if isinstance(error.orig, UniqueViolation):
            raise DuplicateUserError(_duplicate_message(error)) from None

        raise

    db.refresh(user)
    return user
