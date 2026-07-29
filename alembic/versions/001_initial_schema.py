"""Initial MusicBloom schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=False),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("is_demo_user", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_profiles_is_demo_user", "user_profiles", ["is_demo_user"])
    op.create_index("ix_user_profiles_username", "user_profiles", ["username"], unique=True)

    op.create_table(
        "achievement_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("achievement_id", sa.String(length=64), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "achievement_id", name="uq_achievement_progress_user_achievement"),
    )
    op.create_index("ix_achievement_progress_user_id", "achievement_progress", ["user_id"])

    op.create_table(
        "equipped_decorations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("decoration_id", sa.String(length=64), nullable=False),
        sa.Column("slot", sa.String(length=64), nullable=False),
        sa.Column("equipped_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "slot", name="uq_equipped_decorations_user_slot"),
    )
    op.create_index("ix_equipped_decorations_user_id", "equipped_decorations", ["user_id"])

    op.create_table(
        "garden_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("garden_name", sa.String(length=128), nullable=False),
        sa.Column("theme", sa.String(length=64), nullable=False),
        sa.Column("layout_data", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_garden_profiles_user_id", "garden_profiles", ["user_id"], unique=True)

    op.create_table(
        "listening_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("position_ms", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_listening_events_event_type", "listening_events", ["event_type"])
    op.create_index("ix_listening_events_occurred_at", "listening_events", ["occurred_at"])
    op.create_index("ix_listening_events_track_id", "listening_events", ["track_id"])
    op.create_index("ix_listening_events_user_id", "listening_events", ["user_id"])

    op.create_table(
        "player_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("volume_level", sa.Float(), nullable=False),
        sa.Column("shuffle", sa.Boolean(), nullable=False),
        sa.Column("repeat_mode", sa.String(length=8), nullable=False),
        sa.Column("queue_index", sa.Integer(), nullable=True),
        sa.Column("active_track", sa.JSON(), nullable=True),
        sa.Column("queue", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_player_sessions_user_id", "player_sessions", ["user_id"], unique=True)

    op.create_table(
        "quest_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("quest_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "quest_id", name="uq_quest_progress_user_quest"),
    )
    op.create_index("ix_quest_progress_user_id", "quest_progress", ["user_id"])

    op.create_table(
        "user_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("melody_points", sa.Integer(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("total_listening_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_progress_user_id", "user_progress", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_user_progress_user_id", table_name="user_progress")
    op.drop_table("user_progress")
    op.drop_index("ix_quest_progress_user_id", table_name="quest_progress")
    op.drop_table("quest_progress")
    op.drop_index("ix_player_sessions_user_id", table_name="player_sessions")
    op.drop_table("player_sessions")
    op.drop_index("ix_listening_events_user_id", table_name="listening_events")
    op.drop_index("ix_listening_events_track_id", table_name="listening_events")
    op.drop_index("ix_listening_events_occurred_at", table_name="listening_events")
    op.drop_index("ix_listening_events_event_type", table_name="listening_events")
    op.drop_table("listening_events")
    op.drop_index("ix_garden_profiles_user_id", table_name="garden_profiles")
    op.drop_table("garden_profiles")
    op.drop_index("ix_equipped_decorations_user_id", table_name="equipped_decorations")
    op.drop_table("equipped_decorations")
    op.drop_index("ix_achievement_progress_user_id", table_name="achievement_progress")
    op.drop_table("achievement_progress")
    op.drop_index("ix_user_profiles_username", table_name="user_profiles")
    op.drop_index("ix_user_profiles_is_demo_user", table_name="user_profiles")
    op.drop_table("user_profiles")
