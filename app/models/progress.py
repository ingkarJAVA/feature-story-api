"""Database models for Player Progress & Endings (Student 3)."""

from sqlalchemy import Boolean, ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class GameSession(Base):
    """Stores one player's game progress."""

    __tablename__ = "game_sessions"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True
    )
    user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            name="fk_game_sessions_user_id",
            ondelete="CASCADE"
        ),
        nullable=True,
        index=True
    )

    player_name: Mapped[str] = mapped_column(
        String(30),
        nullable=False
    )

    current_scene_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("scenes.id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active"
    )

    ending_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    accused_suspect_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("suspects.id"),
        nullable=True
    )

    accusation_correct: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True
    )

    current_scene: Mapped["Scene"] = relationship(
        "Scene",
        foreign_keys=[current_scene_id]
    )

    choices_history: Mapped[list["SessionChoice"]] = relationship(
        "SessionChoice",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SessionChoice.id"
    )


class SessionChoice(Base):
    """Stores each choice made during a game session."""

    __tablename__ = "session_choices"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    session_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("game_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    choice_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("choices.id"),
        nullable=False
    )

    session: Mapped["GameSession"] = relationship(
        "GameSession",
        back_populates="choices_history"
    )

    choice: Mapped["Choice"] = relationship("Choice")
