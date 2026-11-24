"""Add user ownership to game sessions.

Revision ID: 0007
Revises: 0006
"""

from alembic import op
import sqlalchemy as sa


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "game_sessions",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_game_sessions_user_id",
        "game_sessions",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_index(
        "ix_game_sessions_user_id",
        "game_sessions",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_game_sessions_user_id",
        table_name="game_sessions",
    )

    op.drop_constraint(
        "fk_game_sessions_user_id",
        "game_sessions",
        type_="foreignkey",
    )

    op.drop_column("game_sessions", "user_id")