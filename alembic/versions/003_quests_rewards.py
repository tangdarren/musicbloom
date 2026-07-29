"""Add quest reward claims and decoration unlocks."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "003_quests_rewards"
down_revision: str | None = "002_progression"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "quest_progress",
        sa.Column("period_key", sa.String(length=16), nullable=False, server_default=""),
    )
    op.add_column(
        "quest_progress",
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "achievement_progress",
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "decoration_unlocks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("decoration_id", sa.String(length=64), nullable=False),
        sa.Column("unlocked_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "decoration_id",
            name="uq_decoration_unlocks_user_decoration",
        ),
    )
    op.create_index(
        "ix_decoration_unlocks_user_id",
        "decoration_unlocks",
        ["user_id"],
    )
    op.create_index(
        "ix_decoration_unlocks_decoration_id",
        "decoration_unlocks",
        ["decoration_id"],
    )

    op.create_table(
        "reward_claims",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("reward_id", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("melody_points_granted", sa.Integer(), nullable=False),
        sa.Column("decoration_id", sa.String(length=64), nullable=True),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "source_type",
            "source_id",
            name="uq_reward_claims_user_source",
        ),
    )
    op.create_index("ix_reward_claims_user_id", "reward_claims", ["user_id"])
    op.create_index("ix_reward_claims_reward_id", "reward_claims", ["reward_id"])
    op.create_index("ix_reward_claims_source_type", "reward_claims", ["source_type"])
    op.create_index("ix_reward_claims_source_id", "reward_claims", ["source_id"])
    op.create_index("ix_reward_claims_claimed_at", "reward_claims", ["claimed_at"])


def downgrade() -> None:
    op.drop_index("ix_reward_claims_claimed_at", table_name="reward_claims")
    op.drop_index("ix_reward_claims_source_id", table_name="reward_claims")
    op.drop_index("ix_reward_claims_source_type", table_name="reward_claims")
    op.drop_index("ix_reward_claims_reward_id", table_name="reward_claims")
    op.drop_index("ix_reward_claims_user_id", table_name="reward_claims")
    op.drop_table("reward_claims")

    op.drop_index("ix_decoration_unlocks_decoration_id", table_name="decoration_unlocks")
    op.drop_index("ix_decoration_unlocks_user_id", table_name="decoration_unlocks")
    op.drop_table("decoration_unlocks")

    op.drop_column("achievement_progress", "claimed_at")
    op.drop_column("quest_progress", "claimed_at")
    op.drop_column("quest_progress", "period_key")
