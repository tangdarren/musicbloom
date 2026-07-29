"""Track listening state database entity."""

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from musicbloom.db.base import Base, TimestampMixin


class TrackListeningState(Base, TimestampMixin):
    """Per-track anti-exploit listening progress for a user."""

    __tablename__ = "track_listening_states"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "track_id",
            name="uq_track_listening_states_user_track",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    track_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    validated_listening_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    progress_points_awarded: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    progress_experience_awarded: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    completion_awarded: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    skipped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_position_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
