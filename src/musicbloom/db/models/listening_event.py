"""Listening event database entity."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from musicbloom.db.base import Base, TimestampMixin


class ListeningEvent(Base, TimestampMixin):
    """Historical listening activity for a user."""

    __tablename__ = "listening_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    track_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    position_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
