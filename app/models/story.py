"""Database models for the Story & Scenes module (Student 1)."""
from typing import List

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    genre: Mapped[str] = mapped_column(String(100), nullable=False)
    main_character: Mapped[str] = mapped_column(String(100), nullable=False)

    scenes: Mapped[List["Scene"]] = relationship(back_populates="story")


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    story_id: Mapped[str] = mapped_column(
        ForeignKey("stories.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False, default="Unknown")
    is_ending: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    story: Mapped["Story"] = relationship(back_populates="scenes")
    # Outgoing choices (choices that start in this scene).
    choices: Mapped[List["Choice"]] = relationship(
        back_populates="scene",
        foreign_keys="Choice.scene_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Choice(Base):
    __tablename__ = "choices"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    # Source scene. Deleting the scene deletes its own outgoing choices.
    scene_id: Mapped[str] = mapped_column(
        ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    choice_text: Mapped[str] = mapped_column(String(200), nullable=False)
    # Destination scene. No cascade: the database refuses to delete a scene
    # that other choices still point to.
    next_scene_id: Mapped[str] = mapped_column(
        ForeignKey("scenes.id"), nullable=False, index=True
    )

    scene: Mapped["Scene"] = relationship(
        back_populates="choices", foreign_keys=[scene_id]
    )
