"""Quest progress database entity."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from musicbloom.db.base import Base, TimestampMixin


class QuestProgress(Base, TimestampMixin):
    """Quest completion state for a user."""

    __tablename__ = "quest_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "quest_id", name="uq_quest_progress_user_quest"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    quest_id: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="not_started",
    )
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    period_key: Mapped[str] = mapped_column(String(16), nullable=False, default="")
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
