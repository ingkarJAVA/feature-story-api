"""create discovered_clues (clues found by a game session)

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-20

Needs game_sessions (0003) and clues (0002) to exist first.
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "discovered_clues",
        sa.Column(
            "session_id", sa.String(50),
            sa.ForeignKey("game_sessions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "clue_id", sa.String(60),
            sa.ForeignKey("clues.id"), primary_key=True,
        ),
        sa.Column(
            "discovered_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
    )
    op.create_index("ix_discovered_clues_clue_id", "discovered_clues", ["clue_id"])


def downgrade() -> None:
    op.drop_index("ix_discovered_clues_clue_id", table_name="discovered_clues")
    op.drop_table("discovered_clues")
