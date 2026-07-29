"""Add Spotify OAuth connection storage."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004_spotify_connection"
down_revision: str | None = "003_quests_rewards"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "spotify_connections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("spotify_user_id", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=256), nullable=True),
        sa.Column("encrypted_access_token", sa.Text(), nullable=False),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scopes", sa.String(length=512), nullable=False),
        sa.Column("last_error_code", sa.String(length=64), nullable=True),
        sa.Column("last_error_message", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_spotify_connections_user_id"),
        sa.UniqueConstraint(
            "spotify_user_id",
            name="uq_spotify_connections_spotify_user_id",
        ),
    )
    op.create_index(
        "ix_spotify_connections_user_id",
        "spotify_connections",
        ["user_id"],
    )
    op.create_index(
        "ix_spotify_connections_spotify_user_id",
        "spotify_connections",
        ["spotify_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_spotify_connections_spotify_user_id", table_name="spotify_connections")
    op.drop_index("ix_spotify_connections_user_id", table_name="spotify_connections")
    op.drop_table("spotify_connections")
