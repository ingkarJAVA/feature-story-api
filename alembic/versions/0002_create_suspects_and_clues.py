"""create suspects and clues

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-20

Must run BEFORE game_sessions (0003), because game_sessions.accused_suspect_id
points to suspects.id.
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "suspects",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("motive", sa.String(300), nullable=False),
        sa.Column("alibi", sa.String(300), nullable=False),
        sa.Column("is_guilty", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "clues",
        sa.Column("id", sa.String(60), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(600), nullable=False),
        sa.Column("location", sa.String(100), nullable=False),
        sa.Column(
            "related_scene_id", sa.String(50),
            sa.ForeignKey("scenes.id"), nullable=False,
        ),
        sa.Column("importance", sa.String(10), nullable=False),
        sa.Column(
            "suspect_id", sa.String(50),
            sa.ForeignKey("suspects.id", ondelete="SET NULL"), nullable=True,
        ),
        sa.CheckConstraint(
            "importance IN ('low', 'medium', 'high')", name="ck_clues_importance"
        ),
    )
    op.create_index("ix_clues_related_scene_id", "clues", ["related_scene_id"])
    op.create_index("ix_clues_suspect_id", "clues", ["suspect_id"])


def downgrade() -> None:
    op.drop_index("ix_clues_suspect_id", table_name="clues")
    op.drop_index("ix_clues_related_scene_id", table_name="clues")
    op.drop_table("clues")
    op.drop_table("suspects")
