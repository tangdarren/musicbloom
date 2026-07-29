"""Add progression tables and columns."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_progression"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_progress",
        sa.Column("experience_points", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "user_progress",
        sa.Column("streak_current_days", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "user_progress",
        sa.Column("streak_last_utc_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "user_progress",
        sa.Column(
            "streak_bonus_points_today",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "user_progress",
        sa.Column("streak_bonus_utc_date", sa.Date(), nullable=True),
    )

    op.add_column(
        "listening_events",
        sa.Column("idempotency_key", sa.String(length=64), nullable=True),
    )

    with op.batch_alter_table("listening_events") as batch_op:
        batch_op.create_index(
            "ix_listening_events_idempotency_key",
            ["idempotency_key"],
        )
        batch_op.create_unique_constraint(
            "uq_listening_events_user_idempotency",
            ["user_id", "idempotency_key"],
        )

    op.create_table(
        "track_listening_states",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("track_id", sa.String(length=64), nullable=False),
        sa.Column("validated_listening_ms", sa.Integer(), nullable=False),
        sa.Column("progress_points_awarded", sa.Integer(), nullable=False),
        sa.Column("progress_experience_awarded", sa.Integer(), nullable=False),
        sa.Column("completion_awarded", sa.Boolean(), nullable=False),
        sa.Column("skipped", sa.Boolean(), nullable=False),
        sa.Column("last_position_ms", sa.Integer(), nullable=False),
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
        sa.UniqueConstraint(
            "user_id",
            "track_id",
            name="uq_track_listening_states_user_track",
        ),
    )
    op.create_index(
        "ix_track_listening_states_user_id",
        "track_listening_states",
        ["user_id"],
    )
    op.create_index(
        "ix_track_listening_states_track_id",
        "track_listening_states",
        ["track_id"],
    )

    op.create_table(
        "melody_points_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("experience_amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=64), nullable=False),
        sa.Column("explanation", sa.String(length=512), nullable=False),
        sa.Column("track_id", sa.String(length=64), nullable=True),
        sa.Column("listening_event_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["listening_event_id"],
            ["listening_events.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_melody_points_transactions_user_id",
        "melody_points_transactions",
        ["user_id"],
    )
    op.create_index(
        "ix_melody_points_transactions_reason",
        "melody_points_transactions",
        ["reason"],
    )
    op.create_index(
        "ix_melody_points_transactions_track_id",
        "melody_points_transactions",
        ["track_id"],
    )
    op.create_index(
        "ix_melody_points_transactions_listening_event_id",
        "melody_points_transactions",
        ["listening_event_id"],
    )
    op.create_index(
        "ix_melody_points_transactions_created_at",
        "melody_points_transactions",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_melody_points_transactions_created_at",
        table_name="melody_points_transactions",
    )
    op.drop_index(
        "ix_melody_points_transactions_listening_event_id",
        table_name="melody_points_transactions",
    )
    op.drop_index(
        "ix_melody_points_transactions_track_id",
        table_name="melody_points_transactions",
    )
    op.drop_index(
        "ix_melody_points_transactions_reason",
        table_name="melody_points_transactions",
    )
    op.drop_index(
        "ix_melody_points_transactions_user_id",
        table_name="melody_points_transactions",
    )
    op.drop_table("melody_points_transactions")

    op.drop_index("ix_track_listening_states_track_id", table_name="track_listening_states")
    op.drop_index("ix_track_listening_states_user_id", table_name="track_listening_states")
    op.drop_table("track_listening_states")

    with op.batch_alter_table("listening_events") as batch_op:
        batch_op.drop_constraint(
            "uq_listening_events_user_idempotency",
            type_="unique",
        )
        batch_op.drop_index("ix_listening_events_idempotency_key")
    op.drop_column("listening_events", "idempotency_key")

    op.drop_column("user_progress", "streak_bonus_utc_date")
    op.drop_column("user_progress", "streak_bonus_points_today")
    op.drop_column("user_progress", "streak_last_utc_date")
    op.drop_column("user_progress", "streak_current_days")
    op.drop_column("user_progress", "experience_points")
