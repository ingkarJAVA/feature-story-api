"""create game_sessions, session_choices and session ID sequence (Student 3)

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-20
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "game_sessions",
        sa.Column("id", sa.String(50), primary_key=True),
        sa.Column("player_name", sa.String(30), nullable=False),
        sa.Column(
            "current_scene_id", sa.String(50),
            sa.ForeignKey("scenes.id"), nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("ending_id", sa.String(50), nullable=True),
        sa.Column(
            "accused_suspect_id", sa.String(50),
            sa.ForeignKey("suspects.id"), nullable=True,
        ),
        sa.Column("accusation_correct", sa.Boolean(), nullable=True),
    )
    op.create_table(
        "session_choices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id", sa.String(50),
            sa.ForeignKey("game_sessions.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "choice_id", sa.String(50),
            sa.ForeignKey("choices.id"), nullable=False,
        ),
    )
    op.create_index("ix_session_choices_session_id", "session_choices", ["session_id"])
    # progress_service.create_session() calls nextval('game_session_id_seq').
    op.execute("CREATE SEQUENCE game_session_id_seq START 1")


def downgrade() -> None:
    op.execute("DROP SEQUENCE game_session_id_seq")
    op.drop_index("ix_session_choices_session_id", table_name="session_choices")
    op.drop_table("session_choices")
    op.drop_table("game_sessions")
