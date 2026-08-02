"""Add favorite tracks storage."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005_favorite_tracks"
down_revision: str | None = "004_spotify_connection"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "favorite_tracks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "track_id", name="uq_favorite_tracks_user_track"),
    )
    op.create_index("ix_favorite_tracks_user_id", "favorite_tracks", ["user_id"])
    op.create_index("ix_favorite_tracks_track_id", "favorite_tracks", ["track_id"])


def downgrade() -> None:
    op.drop_index("ix_favorite_tracks_track_id", table_name="favorite_tracks")
    op.drop_index("ix_favorite_tracks_user_id", table_name="favorite_tracks")
    op.drop_table("favorite_tracks")
