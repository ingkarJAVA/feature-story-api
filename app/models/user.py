"""Database model for registered users (Assignment 7, Student 1).

Student 2 (login / JWT) and Student 3 (ownership of game sessions) import
this model:    from app.models.user import User

IMPORTANT: only the password HASH is stored, never the real password.
"""
from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"
    # The database itself refuses duplicates. This is the final protection
    # even if two registrations arrive at exactly the same moment.
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("username", name="uq_users_username"),
    )

    # PostgreSQL generates 1, 2, 3, ... automatically.
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Always stored in lowercase (see app/schemas/auth.py).
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(30), nullable=False)
    # Argon2id hash (about 100 characters). Never the plain password.
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # "user" by default. Student 3 can introduce other roles later.
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="user", server_default="user"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
