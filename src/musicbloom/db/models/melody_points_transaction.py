"""Melody points transaction database entity."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from musicbloom.db.base import Base


class MelodyPointsTransaction(Base):
    """Audit log for melody points awards."""

    __tablename__ = "melody_points_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    experience_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reason: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    explanation: Mapped[str] = mapped_column(String(512), nullable=False)
    track_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    listening_event_id: Mapped[int | None] = mapped_column(
        ForeignKey("listening_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
