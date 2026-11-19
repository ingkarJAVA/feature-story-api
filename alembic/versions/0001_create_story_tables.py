"""create stories, scenes, choices and ID sequences

Revision ID: 0001
Revises:
Create Date: 2026-11-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stories",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("genre", sa.String(100), nullable=False),
        sa.Column("main_character", sa.String(100), nullable=False),
    )
    op.create_table(
        "scenes",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("story_id", sa.String(50), sa.ForeignKey("stories.id"), nullable=False),
        sa.Column("title", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location", sa.String(100), nullable=False),
        sa.Column("is_ending", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_scenes_story_id", "scenes", ["story_id"])
    op.create_table(
        "choices",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column(
            "scene_id", sa.String(50),
            sa.ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("choice_text", sa.String(200), nullable=False),
        sa.Column(
            "next_scene_id", sa.String(50), sa.ForeignKey("scenes.id"), nullable=False
        ),
    )
    op.create_index("ix_choices_scene_id", "choices", ["scene_id"])
    op.create_index("ix_choices_next_scene_id", "choices", ["next_scene_id"])

    # Sequences give unique numbers for scene_16, choice_31, ... even after
    # restarts and for concurrent requests. Numbers are never reused.
    op.execute("CREATE SEQUENCE scene_id_seq START 1")
    op.execute("CREATE SEQUENCE choice_id_seq START 1")


def downgrade() -> None:
    op.execute("DROP SEQUENCE choice_id_seq")
    op.execute("DROP SEQUENCE scene_id_seq")
    op.drop_index("ix_choices_next_scene_id", table_name="choices")
    op.drop_index("ix_choices_scene_id", table_name="choices")
    op.drop_table("choices")
    op.drop_index("ix_scenes_story_id", table_name="scenes")
    op.drop_table("scenes")
    op.drop_table("stories")
