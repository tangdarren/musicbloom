"""User progress database entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from musicbloom.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from musicbloom.db.models.user_profile import UserProfile


class UserProgress(Base, TimestampMixin):
    """Gamification progress for a user."""

    __tablename__ = "user_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    melody_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_listening_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped[UserProfile] = relationship(back_populates="progress")
