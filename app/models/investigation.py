"""Database models for the Investigation module (Student 2).

Tables:
    suspects          - the people who can be accused
    clues             - evidence found in scenes (FK -> scenes.id)
    discovered_clues  - which clue was found in which game session
                        (FK -> game_sessions.id and clues.id)
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, ForeignKey, String, func,
)
from sqlalchemy.orm import Mapped, backref, mapped_column, relationship

from app.database import Base


class Suspect(Base):
    __tablename__ = "suspects"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    motive: Mapped[str] = mapped_column(String(300), nullable=False)
    alibi: Mapped[str] = mapped_column(String(300), nullable=False)
    # Never returned by the public API (see SuspectOut).
    is_guilty: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # One suspect can be linked to many clues (optional link).
    clues: Mapped[List["Clue"]] = relationship(
        back_populates="suspect", passive_deletes=True
    )


class Clue(Base):
    __tablename__ = "clues"
    __table_args__ = (
        CheckConstraint(
            "importance IN ('low', 'medium', 'high')", name="ck_clues_importance"
        ),
    )

    id: Mapped[str] = mapped_column(String(60), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(600), nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)
    # A Scene can have many Clues. (Student 1's Scene model gets a `clues`
    # attribute automatically through the backref below.)
    related_scene_id: Mapped[str] = mapped_column(
        ForeignKey("scenes.id"), nullable=False, index=True
    )
    importance: Mapped[str] = mapped_column(String(10), nullable=False)
    # Optional: which suspect this clue points to. NULL = not linked.
    suspect_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("suspects.id", ondelete="SET NULL"), nullable=True, index=True
    )

    scene = relationship("Scene", backref="clues")
    suspect: Mapped[Optional["Suspect"]] = relationship(back_populates="clues")


class DiscoveredClue(Base):
    """One row = "this clue was found in this game session"."""

    __tablename__ = "discovered_clues"

    # Composite primary key: the same clue can never be stored twice
    # for the same session.
    session_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("game_sessions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    clue_id: Mapped[str] = mapped_column(
        String(60), ForeignKey("clues.id"), primary_key=True, index=True
    )
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # A GameSession can have many discovered clues (GameSession.discovered_clues).
    session = relationship(
        "GameSession",
        backref=backref(
            "discovered_clues", cascade="all, delete-orphan", passive_deletes=True
        ),
    )
    clue: Mapped["Clue"] = relationship()
